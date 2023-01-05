import os
from .couch import CouchClient as CouchClient
from .field_client import FieldDatabase
from .easydb_client import EasydbClient
from . import global_settings
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
        self.edb_client = edb_client
    
    def process_request(self, *args, **kwargs):
        self.logger.debug(f"Handler: {self.__class__.__name__}")
        self.logger.debug(f"Full data: {self.full_data}")
        self.logger.debug(f'Object data {self.object_data}')
        return self.full_data


class DbCreatingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        self.logger.debug(f'Handling {self.inner_data}')
        couch = CouchClient(global_settings.Couch.HOST_URL, auth_from_module=True)
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
        return database

class ImportInitiatingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        result = self.object_data[global_settings.Easydb.IMPORT_RESULT_FIELD]
        self.logger.debug(self.object_data)
        if not result:
            self.object_data[global_settings.Easydb.IMPORT_RESULT_FIELD] = global_settings.Easydb.IMPORT_REGISTRATION_MESSAGE
        
        return self.full_data

class FileImportingHandler(EdbHandler):
    def process_request(self, *args, **kwargs):
        super().process_request()
        self.edb_client.acquire_session()
        id = self.object_data['_id']
        try:
            wrapped_object_data = self.edb_client.get_object_by_id(self.object_type, id)
        except ValueError as error:
            self.logger.exception(error)
            self.edb_client.update_item(self.object_type,id, {global_settings.Easydb.IMPORT_RESULT_FIELD: 
                                                              global_settings.Easydb.IMPORT_INITIATION_MESSAGE})

        
        inner_object_data = wrapped_object_data[self.object_type]
        self.logger.debug(f'Retrieved from edb: {wrapped_object_data}')
        import_result = inner_object_data[global_settings.Easydb.IMPORT_RESULT_FIELD]
        if import_result != global_settings.Easydb.IMPORT_REGISTRATION_MESSAGE:
            return
        try:
            import_file = EasydbClient.get_preferred_media(wrapped_object_data,
                                                           global_settings.Easydb.FIELD_IMPORT_MEDIA_FIELD)
            
            file_url = dp.get(import_file, 'versions/original/download_url')
            self.logger.debug(file_url)
        except KeyError:
            self.logger.debug(f'No media associated with {self.object_type} {id}.')
            self.edb_client.update_item(self.object_type, id, {global_settings.Easydb.IMPORT_RESULT_FIELD:
                                                               global_settings.Easydb.IMPORT_FAILURE_MESSAGE})
            return self.full_data
        
        self.logger.debug(f'acquired url {file_url}')
        
        self.edb_client.update_item(self.object_type,id, {global_settings.Easydb.IMPORT_RESULT_FIELD:
                                                          global_settings.Easydb.IMPORT_INITIATION_MESSAGE})
                
        
        return self.full_data

