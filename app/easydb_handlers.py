import os, json
from dotenv import load_dotenv
from dpath import util as dp

from app import settings
from app.couchdb.server import CouchDBServer
from app.field.database import FieldDatabase
from app.field.hub import FieldHub


load_dotenv()

COUCH_HOST = ""
COUCHDB_ADMIN_USER = os.getenv('COUCHDB_ADMIN_USER')
COUCHDB_ADMIN_PASSWORD = os.getenv('COUCHDB_ADMIN_PASSWORD')


class EasyDBHandler:
    def __init__(self, incoming_request, logger, easydb):
        self.full_data = incoming_request.get_json()
        self.inner_data = self.full_data['data']
        self.object_type = self.inner_data['_objecttype']
        self.object_data = self.inner_data[self.object_type]
        self.logger = logger
        self.logger.debug(f"Created handler for object: \n\n{json.dumps(self.full_data, indent=2)}")
        self.easydb = easydb
    
    def process_request(self, *args, **kwargs):
        self.logger.debug(f"Handler: {self.__class__.__name__}")
        self.logger.debug(f"Full data: {self.full_data}")
        self.logger.debug(f'Object data {self.object_data}')
        return self.full_data


class VorgangHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        if self.__is_field_project_required():
            identifier = self.__create_field_project_identifier()
            self.logger.debug(f'Creating new Field project "{identifier}"')
            self.easydb.acquire_session()
            self.__validate_project_identifier(identifier)
            password = self.__create_field_project(identifier)
            self.__create_easydb_object(identifier, password)
        return self.full_data

    def __is_field_project_required(self):
        ancestors = self.object_data['lk_vorgang_kategorie']['conceptAncestors']
        # TODO Move to settings
        return '76f1f241-6425-4fd3-a93c-ee88a47affc1' in ancestors

    def __create_field_project_identifier(self):
        return self.object_data['vorgang'].lower().strip()

    def __validate_project_identifier(self, identifier):
        if self.easydb.get_item('field_database', 'db_name', identifier) != None:
            raise ValueError(f'Field database "{identifier}" already exists.')
        CouchDBServer.check_db_name(identifier, True)

    def __create_field_project(self, identifier):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = hub.create_project(identifier)
        return password

    def __create_easydb_object(self, identifier, password):
        fields_data = {
            'db_name': identifier,
            'password': password,
            'lk_vorgang': self.inner_data
        }

        self.easydb.create_object('field_database', fields_data)


class ImportInitiatingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        result = self.object_data[settings.Easydb.IMPORT_RESULT_FIELD]
        self.logger.debug(self.object_data)
        if not result:
            self.object_data[settings.Easydb.IMPORT_RESULT_FIELD] = settings.Easydb.IMPORT_REGISTRATION_MESSAGE
        
        return self.full_data

class FileImportingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = self.object_data['password']

        self.easydb.acquire_session()
        files = self.easydb.get_files_from_object(self.object_data, self.object_type)
        self.logger.debug(files)

        for file in files:
            # TODO Read db name from image file
            db_name = ''
            database = FieldDatabase(hub, db_name, password)

            if file['mime_type'] in settings.EdbHandlers.IMAGE_IMPORT_MIME_TYPES:
                self.logger.debug(f"Image import: {file['name']}")
                database.ingest_image_from_url(file['url'], file['name'])
            if file['mime_type'] in settings.EdbHandlers.CSV_IMPORT_MIME_TYPES:
                self.logger.debug(f"CSV import: {file['name']}")
            if file['mime_type'] in settings.EdbHandlers.SHAPEFILE_IMPORT_MIME_TYPES:
                self.logger.debug(f"Shapefile import: {file['name']}")
    
        return self.full_data
