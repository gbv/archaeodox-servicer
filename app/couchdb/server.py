import json, os, requests, string, random, re
from dpath import util as dp

from app import credentials
from app.couchdb.database import CouchDatabase


class CouchDBServer:
    def __init__(self, host, user_name=None, password=None, auth_from_module=False) -> None:
        self.session = requests.Session()
        if auth_from_module:
            user_name = credentials.COUCHDB_ADMIN_USER
            password = credentials.COUCHDB_ADMIN_PASSWORD
        self.set_auth(user_name, password)
        self.host = host
        
    def set_auth(self, user_name, password):
        self.auth = (user_name, password)
        self.session.auth = self.auth
  
    def get_config(self, database):
        url = os.path.join(self.host, database, CouchDBServer.CONFIG_DOCUMENT)
        response = requests.get(url=url, auth=self.auth)
        if response.ok:
            return response.json()

    def inject_config(self, database, path, patch):
        config = self.get_config(database)
        dp.new(config, path, patch)
        url = self.prepend_host(database, CouchDBServer.CONFIG_DOCUMENT)
        response = requests.put(url=url, data=json.dumps(config), auth=self.auth)
        return response.content

    @staticmethod
    def generate_password(length=32):
        pool = string.ascii_letters + string.digits
        return ''.join([random.choice(pool) for i in range(length)])

    def has_database(self, database_name):
        database_url = self.prepend_host(database_name)
        reply = requests.get(database_url, auth=self.auth)
        return reply.ok
    
    def prepend_host(self, *args):
        return os.path.join(self.host, *args)

    @classmethod
    def check_db_name(cls, db_name):
        valid = re.match(r'^[a-z][a-z0-9_()-]*$', db_name)
        if not valid:
            raise ValueError('The project name may only contain lower case letters and characters _, (, ), - and must start with a letter.')
        return valid

    def create_database(self, db_name):
        db_name = db_name.lower()
        CouchDBServer.check_db_name(db_name)
            
        response = requests.put(url=self.prepend_host(db_name), auth=self.auth)
        if not response.ok:
            raise ConnectionError(response.content)
        database = CouchDatabase(self, db_name)
        return database
        
    def drop_db(self, db_name):
        response = requests.delete(self.prepend_host(db_name), auth=self.auth)
        return response.ok
    
    def create_db_user(self, db_name, user_name):
        user_id = f'org.couchdb.user:{user_name}'
        user = {
            'name': user_name,
            'type': 'user',
            'roles': [],
            'password': CouchDBServer.generate_password()
        }
        response = requests.put(url=self.prepend_host('_users', user_id),
                                                 data=json.dumps(user),
                                                 auth=self.auth)
        if not response.ok:
            raise ConnectionError('Failed to create user ' + db_name + '\n' + str(response.content))
        return user
        
    def add_user_to_db(self, user_name, db_name):
        security = {'admins': 
                      {'names': [],
                       'roles': []
                       },
                    'members':
                      {'names': [user_name],
                       'roles': []
                       }
                   }
        response = requests.put(self.prepend_host(db_name, '_security'),
                                data=json.dumps(security),
                                auth=self.auth)
        if not response.ok:
            raise ConnectionError(str(response.content))
        return response.ok
    
    def create_db_and_user(self, db_name, user_name=None):
        if user_name is None:
            user_name = db_name
        
        database = self.create_database(db_name)
        user = self.create_db_user(db_name, user_name)
        self.add_user_to_db(user_name, db_name)
        return database, user
