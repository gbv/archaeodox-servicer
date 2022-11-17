import csv, json, mimetypes, requests, io
from uuid import uuid4
from os.path import basename

from .couch import CouchClient
from dpath import util as dp
from PIL import Image


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
            if value:
                sanitized[key] = value
        return sanitized
                
    @staticmethod
    def process(row):
        row = CSV.remove_empties(row)
        return CSV.inflate(row)



class FieldClient(CouchClient):
    OBJECT_TYPES = ['Feature',
                'Befundanschnitt',
                'Befundkomplex',
                'Profile',
                'Find',
                'Planum',
                'Place',
                'Project',
                'Sample',
                'Trench',
                'Drawing',
                'Photo']

    def __init__(self, host, database, user_name=None, password=None, auth_from_env=False) -> None:
        super().__init__(host, user_name, password, auth_from_env)
        self.database = database

    def has_database(self, database_name):
        self.database == database_name

    def get_or_create_id(self, identifier, field='resource'):
        mango =  {'selector': {f'{field}.identifier': identifier},
                  'fields': [field, '_id']
                  }
        search_results = requests.post(self.prepend_host(self.database, '_find'), auth=self.auth, json=mango)
        if search_results.ok:
            documents = search_results.json()['docs']
            if documents:
                return documents[0]['_id']
            else:
                id = str(uuid4())
                document = {'resource': {'identifier': identifier, 'id': id}}
                self.put_doc(self.database, id, document)
                return id
        else:
            raise ValueError(search_results.json()['reason'])

   
    def upload_image(self, image_file_name):
        identifier = self.get_or_create_id(image_file_name)
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
        id = self.get_or_create_id(identifier)
        resource_data['id'] = id
        resource_data['type'] = resource_type
        relations = resource_data.get('relations', {})
        for relation, target in relations.items():
            try:
                target_identifiers = target.split(';')
                target_ids = [self.get_or_create_id(identifier) for identifier in target_identifiers]
                resource_data['relations'][relation] = target_ids
            except:
                raise
        
        return self.update_doc(self.database, id, {'resource': resource_data})
 
    def ingest_csv(self, import_file, import_file_name):
        with import_file:
            feature_reader = csv.DictReader(import_file, delimiter=',', quotechar='"')
            items = [CSV.inflate(item) for item in feature_reader]
        possible_type = list(filter(lambda t: t.lower() in import_file_name, cls.OBJECT_TYPES))
        if possible_type:
            resource_type = possible_type[0]
            for item in items:
                self.populate_resource(item, resource_type)
        else:
            raise ValueError(f'No valid type in {file_name}!')

    def ingest_from_url(self, url):
        response = requests.get(url)
        if response.ok:
            file_object = io.StringIO(response.content)
            file_name = basename.url
            self.ingest_csv(file_object, file_name)
        else:
            raise ValueError(response.text)

            
    
