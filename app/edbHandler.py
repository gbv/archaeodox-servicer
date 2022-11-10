import os
from .couch import Client as CouchClient
from dotenv import load_dotenv

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
        self.logger.debug(f'Handling {self.object_data}')
        return self.full_data


class DbCreatingHandler(EdbHandler):
    def process_request(self):
        self.logger.debug(f'Handling {self.inner_data}')
        couch = CouchClient(COUCH_HOST, auth_from_env=True)
        database = self.object_data
        database_name = database['db_name']

        if not database['password']:
            self.logger.info(f"No credentials for {database_name} found, rectifying this.")
            if couch.has_database(database_name=database_name):
                self.logger.info("Creaitng database and user.")
                user = couch.create_db_user(database_name, database_name)
                couch.add_user_to_db(user['name'], database_name)  
            else:
                self.logger.info("Creaitng user.")
                user = couch.create_db_and_user(database_name, database_name)
            
            database['password'] = user['password']

        return self.full_data
