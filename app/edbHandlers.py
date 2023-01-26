import os, json
from .couch import CouchDBServer
from .field_client import FieldDatabase, FieldHub
from .easydb_client import EasydbClient
from . import settings
from dotenv import load_dotenv
from dpath import util as dp


load_dotenv()

COUCH_HOST = ""
COUCHDB_ADMIN_USER = os.getenv('COUCHDB_ADMIN_USER')
COUCHDB_ADMIN_PASSWORD = os.getenv('COUCHDB_ADMIN_PASSWORD')


class EdbHandler:
    def __init__(self, incoming_request, logger, edb_client):
        self.full_data = incoming_request.get_json()
        self.inner_data = self.full_data['data']
        self.object_type = self.inner_data['_objecttype']
        self.object_data = self.inner_data[self.object_type]
        self.logger = logger
        self.logger.debug(f"Created handler for object: \n\n{json.dumps(self.full_data, indent=2)}")
        self.edb_client = edb_client
    
    def process_request(self, *args, **kwargs):
        self.logger.debug(f"Handler: {self.__class__.__name__}")
        self.logger.debug(f"Full data: {self.full_data}")
        self.logger.debug(f'Object data {self.object_data}')
        return self.full_data


class DbCreatingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        self.logger.debug(f'Handling {self.inner_data}')
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        database = self.object_data
        database_name = database['db_name'].lower().strip()
        CouchDBServer.check_db_name(database_name, True)
        
        database['db_name'] = database_name

        if not database['password']:
            self.logger.info(f"No credentials for {database_name} found, rectifying this.")
            database['password'] = hub.create_project(database_name)
        return self.full_data

class ImportInitiatingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        result = self.object_data[settings.Easydb.IMPORT_RESULT_FIELD]
        self.logger.debug(self.object_data)
        if not result:
            self.object_data[settings.Easydb.IMPORT_RESULT_FIELD] = settings.Easydb.IMPORT_REGISTRATION_MESSAGE
        
        return self.full_data

class FileImportingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = self.object_data['password']

        files = self.edb_client.get_files_from_object(self.object_data, self.object_type)
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

