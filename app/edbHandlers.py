import os
from .couch import CouchClient as CouchClient
from .field_client import FieldClient
from .easydb_client import EasydbClient
from dotenv import load_dotenv
from dpath import util as dp


load_dotenv()

COUCH_HOST = "http://esx-80.gbv.de:5984"
COUCHDB_ADMIN_USER = os.getenv('COUCHDB_ADMIN_USER')
COUCHDB_ADMIN_PASSWORD = os.getenv('COUCHDB_ADMIN_PASSWORD')


class EdbHandler:
    def __init__(self, incoming_request, logger):
        self.full_data = incoming_request.get_json()
        self.inner_data = self.full_data['data']
        self.object_type = self.inner_data['_objecttype']
        self.object_data = self.inner_data[self.object_type]
        self.logger = logger
    
    def process_request(self):
        self.logger.debug(f"Handler: {self.__class__.__name__}")
        self.logger.debug(f"Full data: {self.full_data}")
        self.logger.debug(f'Object data {self.object_data}')
        return self.full_data


class DbCreatingHandler(EdbHandler):
    def process_request(self):
        self.logger.debug(f'Handling {self.inner_data}')
        couch = CouchClient(COUCH_HOST, auth_from_env=True)
        database = self.object_data
        database_name = database['db_name'].lower().strip()
        CouchClient.check_db_name(database_name, True)
        
        database['db_name'] = database_name

        if not database['password']:
            self.logger.info(f"No credentials for {database_name} found, rectifying this.")
            if couch.has_database(database_name=database_name):
                self.logger.info("Creating database and user.")
                user = couch.create_db_user(database_name, database_name)
                couch.add_user_to_db(user['name'], database_name)  
            else:
                self.logger.info("Creating user.")
                user = couch.create_db_and_user(database_name)
            
            database['password'] = user['password']


class ImportInitiatingHandler(EdbHandler):
    INITIATION_MESSAGE = 'Import vorbereitet.'
    RESULT_FIELD = 'import_result'
    
    def process_request(self):
        result = self.object_data[ImportInitiatingHandler.RESULT_FIELD]
        self.logger.debug(self.object_data)
        if not result:
            self.object_data[ImportInitiatingHandler.RESULT_FIELD] = ImportInitiatingHandler.INITIATION_MESSAGE
        
        return self.full_data

class FileImportingHandler(EdbHandler):
    def process_request(self):
        super().process_request()
        easydb_client = EasydbClient('https://hekate.gbv.de', self.logger)
        easydb_client.acquire_session()

        id = self.object_data['_id']
        dump = easydb_client.get_by_id(self.object_type, id, delay=40)
        self.logger.debug(f'Retrieved from edb: {dump}')
        file_url = dp.get(dump, 'project_dump/versions/original/download_url')

        return self.full_data

