import csv, json, mimetypes, requests, io
from uuid import uuid4
from os.path import basename
from datetime import datetime, timezone

from . import couch, global_settings
from dpath import util as dp
from PIL import Image

def iso_utc():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

class CSV:
    @staticmethod
    def inflate(row):
        nested_keys = list(filter(lambda k: '.' in k, row.keys()))
        for key in nested_keys:
            dp.new(row, key, row[key], separator='.')
            row.pop(key)
        return row
    
    @staticmethod
    def remove_empties(row):
        sanitized = {}
        for key, value in row.items():
            if str(value).strip():
                sanitized[key] = value
        return sanitized
                
    @staticmethod
    def process(row):
        row = CSV.remove_empties(row)
        return CSV.inflate(row)


class FieldHub(couch.CouchDBServer):
    CONFIG_DOCUMENT = 'configuration'
    PROJECT_DOCUMENT_ID = 'project'
    
    def __init__(self, host, template_project_name, user_name=None, password=None, auth_from_module=False) -> None:
        super().__init__(host, user_name, password, auth_from_module)
        self.template = couch.CouchDatabase(self, template_project_name)

    def get_config(self):
        return self.template.get_doc(FieldHub.CONFIG_DOCUMENT).json()

    def create_project(self, project_id):
        database, user = self.create_db_and_user(project_id, project_id)
        config = self.get_config()
        database.create_doc(FieldHub.CONFIG_DOCUMENT, config)
        project = {'resource': {
            'identifier': project_id,
            'id': FieldHub.PROJECT_DOCUMENT_ID,
            'category': 'Project'
        }}
        database.create_doc(FieldHub.PROJECT_DOCUMENT_ID, project)
        return user

class FieldDatabase(couch.CouchDatabase):
    OBJECT_TYPES = ['Feature',
                    'Befundanschnitt',
                    'Befundkomplex',
                    'Find',
                    'Planum',
                    'Place',
                    'Project',
                    'Sample',
                    'Trench',
                    'Drawing',
                    'Photo',
                    'Profile']

    def __init__(self, server, name):
        super().__init__(server, name)
        self.media_url = f'{global_settings.FieldHub.MEDIA_URL}/{self.name}/'

    def get_or_create_document(self, identifier):
        mango =  {'selector': {f'resource.identifier': identifier}}
        search_results = self.session.post(self.search_url, json=mango)
        if search_results.ok:
            documents = search_results.json()['docs']
            if documents:
                return documents[0]
            else:
                id = str(uuid4())
                document = {'_id': id,
                            'resource': {'identifier': identifier,
                            'id': id},
                            'created':{'user':'easydb', 'date': iso_utc()},
                            'modified':[]}
                response = self.create_doc(id, document)
                document['_rev'] = response.json()['rev']
                return document
        else:
            raise ValueError(search_results.json()['reason'])

   
    def upload_image(self, image_file_name):
        identifier = self.get_or_create_document(image_file_name)['_id']
        image = Image.open(image_file_name)
        width, height = image.size
        meta_data = self.database[identifier]
        resource = meta_data['resource']
        resource['width'] = width
        resource['height'] = height
        resource['originalFilename'] = image_file_name
        
        mimetype, encoding = mimetypes.guess_type(image_file_name)
        if mimetype is None:
            return
        headers = {'Content-type': mimetype}
        params = {'type': 'original_image'}
        target_url = self.media_url + identifier
        
        response = requests.put(target_url,
                                headers=headers,
                                params=params,
                                auth=self.auth,
                                data=open(image_file_name, 'rb'))
        if response.ok:
            self.database[identifier] = meta_data

    def populate_resource(self, resource_data, resource_type):
        identifier = resource_data['identifier']
        document = self.get_or_create_document(identifier)
        id = document['_id']
        
        resource_data['id'] = id
        resource_data['type'] = resource_type
        relations = resource_data.get('relations', {})
        for relation, target in relations.items():
            target_identifiers = target.split(';')
            target_ids = [self.get_or_create_document(identifier)['_id'] for identifier in target_identifiers]
            resource_data['relations'][relation] = target_ids
            
        document['resource'] = resource_data
        return self.update_doc(id, document=document)
 
    def ingest_csv(self, import_file, import_file_name):
        with import_file:
            feature_reader = csv.DictReader(import_file, delimiter=',', quotechar='"')
            items = [CSV.process(item) for item in feature_reader]
        possible_type = list(filter(lambda t: t.lower() in import_file_name, FieldDatabase.OBJECT_TYPES))
        if possible_type:
            resource_type = possible_type[0]
            for item in items:
                self.populate_resource(item, resource_type)
        else:
            raise ValueError(f'No valid type in {import_file_name}!')

    def ingest_from_url(self, url):
        response = requests.get(url)
        if response.ok:
            file_object = io.StringIO(response.content.decode('utf-8'))
            file_name = basename(url)
            self.ingest_csv(file_object, file_name)
        else:
            raise ValueError(response.text)

    def ingest_shp(self, zipped_shapes):
        converter_response = requests.post(global_settings.GeometryParser.CONVERSION_URL,
                                           files={zipped_shapes: open(zipped_shapes, 'rb')})
        for feature in converter_response.json()['features']:
            feature_properties = feature['properties']
            resource_type = 'Unknown'
            if 'Befunde' in feature_properties['source_file']:
                feature_identifier = global_settings.GeometryParser.FIND_SECTION_ID_TEMPLATE.format(**feature_properties)
                resource_type = 'Befundanschnitt'
            else:
                feature_identifier = feature_properties['id']

            feature_properties['identifier'] = feature_identifier

            for source, target in global_settings.GeometryParser.PROPERTY_MAP.items():
                copied_value = feature_properties.get(source, None)
                if not copied_value is None:
                    feature_properties[target] = copied_value
                    feature_properties.pop(source)
            feature_properties['geometry'] = feature['geometry']
            print(self.populate_resource(CSV.inflate(feature_properties), resource_type).content)