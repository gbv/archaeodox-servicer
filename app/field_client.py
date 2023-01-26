import csv, json, mimetypes, requests, io
from uuid import uuid4
from os.path import basename
from datetime import datetime, timezone
from zipfile import ZipFile

from . import couch
from . import settings
from . import credentials
from .dante import DanteVocabulary
from . import shapefile_converter
from dpath import util as dp
from PIL import Image
from geotiff import GeoTiff


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
    ARCHAEODOX_VOCABULARY_URI_BASE = 'http://uri.gbv.de/terminology'
    ARCHAEODOX_VOCABULARY_NAMES = [
        'amh_material',
        'amh_datierung',
        'amh_objektbezeichnung',
        'amh_warenart'
        #'amh_befunde' Not public yet
    ]
    ARCHAEODOX_VOCABULARY_PREFIX = 'amh-default'
    
    def __init__(self, host, template_project_name, user_name=None, password=None, auth_from_module=False, logger=None) -> None:
        super().__init__(host, user_name, password, auth_from_module)
        self.template = couch.CouchDatabase(self, template_project_name, credentials.COUCHDB_ADMIN_USER, credentials.COUCHDB_ADMIN_PASSWORD)
        self.logger = logger

    def get_config(self):
        return self.template.get_doc(FieldHub.CONFIG_DOCUMENT).json()

    def update_config(self, configuration_document):
        self.template.update_doc(FieldHub.CONFIG_DOCUMENT, configuration_document)

    def create_project(self, project_identifier):
        creation_info = requests.post(f'{settings.FieldHub.PROJECT_URL}/{project_identifier}',
                                      auth=self.auth).json()
        database = couch.CouchDatabase(self, project_identifier)
        
        database.create_doc(FieldHub.CONFIG_DOCUMENT, self.create_configuration_document())
        project = self.create_project_document(project_identifier)
        database.create_doc(FieldHub.PROJECT_DOCUMENT_ID, project)
        return creation_info['info']['password']

    def create_configuration_document(self):
        return {
            '_id': FieldHub.CONFIG_DOCUMENT,
            'resource': self.get_config()['resource'],
            'created': {'user': 'easydb', 'date': iso_utc()},
            'modified': []
        }

    def create_project_document(self, project_identifier):
        return {
            '_id': FieldHub.PROJECT_DOCUMENT_ID,
            'resource': {
                'identifier': project_identifier,
                'id': FieldHub.PROJECT_DOCUMENT_ID,
                'category': 'Project',
                'relations': {}
            },
            'created': {'user': 'easydb', 'date': iso_utc()},
            'modified': []
        }

    def update_valuelists(self):
        configuration_document = self.get_config()
        for vocabulary_name in FieldHub.ARCHAEODOX_VOCABULARY_NAMES:
            if self.logger: self.logger.debug(f'Updating valuelist for vocabulary: {vocabulary_name}')
            vocabulary = DanteVocabulary.from_uri(f'{FieldHub.ARCHAEODOX_VOCABULARY_URI_BASE}/{vocabulary_name}/')
            field_list = vocabulary.get_field_list()
            valuelist_name = f'{FieldHub.ARCHAEODOX_VOCABULARY_PREFIX}:{vocabulary_name}'
            configuration_document['resource']['valuelists'][valuelist_name] = field_list
        self.update_config(configuration_document)


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

    def __init__(self, server, name, password):
        super().__init__(server, name, name, password)
        self.media_url = f'{settings.FieldHub.MEDIA_URL}/{self.name}/'

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
                            'resource': {
                                'identifier': identifier,
                                'id': id,
                                'relations': {}
                            },
                            'created':{'user':'easydb', 'date': iso_utc()},
                            'modified':[]}
                response = self.create_doc(id, document)
                document['_rev'] = response.json()['rev']
                return document
        else:
            raise ValueError(search_results.json()['reason'])

    @staticmethod
    def generate_thumbnail(pil_image_object, format):
        cloned_image = pil_image_object.copy()
        cloned_image.thumbnail((10 * settings.FieldHub.THUMBNAIL_HEIGHT, settings.FieldHub.THUMBNAIL_HEIGHT))
        out_bytes = io.BytesIO()
        cloned_image.save(out_bytes, format)
        return out_bytes


    def upload_image(self, image_object, image_name):
        image_document = self.get_or_create_document(image_name)
        id = image_document['_id']
        image = Image.open(io.BytesIO(image_object.getvalue()))
        FieldDatabase.initialize_image_document(image_document, image_name, image)

        mimetype, encoding = mimetypes.guess_type(image_name)
        if mimetype is None:
            return
        if mimetype == 'image/tiff':
            FieldDatabase.append_georeference(image_document, image_object)

        format = basename(mimetype)
        headers = { 'Content-type': mimetype }
        target_url = self.media_url + id
        
        response = self.upload_original_image(image, format, headers, target_url)
        if response.ok:
            self.upload_thumbnail_image(image, format, headers, target_url)
        else:
            raise ConnectionError(response.content)
        print(response.content)
        self.update_doc(id, image_document)
        

    @staticmethod
    def initialize_image_document(image_document, image_file_name, image):
        width, height = image.size
        resource = image_document['resource']
        if 'category' not in resource:
            # TODO Set correct category or remove if CSV import is mandatory
            resource['category'] = 'Image' 
        resource['width'] = width
        resource['height'] = height
        resource['originalFilename'] = image_file_name
        if 'relations' not in resource:
            resource['relations'] = {}

        
    def upload_original_image(self, image, format, headers, target_url):
        params = { 'type': 'original_image' }
        with io.BytesIO() as image_bytes:
            image.save(image_bytes, format)
            return requests.put(target_url,
                                headers=headers,
                                params=params,
                                auth=self.auth,
                                data=image_bytes.getvalue())
                        
    
    def upload_thumbnail_image(self, image, format, headers, target_url):
        thumbnail_bytes = FieldDatabase.generate_thumbnail(image, format)
        params = { 'type': 'thumbnail_image' }
        with thumbnail_bytes:
            return requests.put(target_url,
                                headers=headers,
                                params=params,
                                auth=self.auth,
                                data=thumbnail_bytes.getvalue())
            

    @staticmethod
    def append_georeference(image_document, image_data):
        width = image_document['resource']['width']
        height = image_document['resource']['height']

        try:
            geotiff = GeoTiff(io.BytesIO(image_data.getvalue()))
            original_crs = geotiff.crs_code
            geotiff = GeoTiff(io.BytesIO(image_data.getvalue()), as_crs=original_crs)

            upper_left = geotiff.get_coords(0, height)
            upper_right = geotiff.get_coords(width, height)
            lower_left = geotiff.get_coords(0, 0)
        
            image_document['resource']['georeference'] = {'topLeftCoordinates': [upper_left[1], upper_left[0]],
                                                      'topRightCoordinates': [upper_right[1], upper_right[0]],
                                                      'bottomLeftCoordinates': [lower_left[1], lower_left[0]]
                                                      }
        except Exception as error:
            logger.error(error)
            pass


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

    def ingest_image_from_url(self, url, name):
        response = requests.get(url)
        if response.ok:
            file_object = io.BytesIO(response.content)
            self.upload_image(file_object, name)
        else:
            raise ValueError(response.text)

    def ingest_shp_from_url(self, url):
        response = requests.get(url)
        if response.ok:
            file_bytes = io.BytesIO(response.content)
            zip_file = ZipFile(file_bytes, 'r')
            self.ingest_shp(zip_file)
        else:
            raise ValueError(response.text)

    def ingest_shp(self, shp_zip_file):
        geojson = shapefile_converter.to_geojson(shp_zip_file)
        for feature in geojson['features']:
            feature_properties = feature['properties']
            resource_type = 'Unknown'
            if 'Befunde' in feature_properties['source_file']:
                feature_identifier = settings.GeometryParser.FIND_SECTION_ID_TEMPLATE.format(**feature_properties)
                resource_type = 'FeatureSegment'
            else:
                feature_identifier = feature_properties['id']

            resource = {}
            resource['identifier'] = feature_identifier
            
            for source, target in settings.GeometryParser.PROPERTY_MAP.items():
                copied_value = feature_properties.get(source, None)
                
                if not copied_value is None:
                    resource[target] = copied_value
            resource['geometry'] = feature['geometry']
            print(self.populate_resource(CSV.inflate(resource), resource_type).content)
