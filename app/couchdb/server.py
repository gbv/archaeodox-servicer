import json, os, requests, string, random, re
from dpath import util as dp

from app import settings
from app.couchdb.database import CouchDatabase


class CouchDBServer:
    def __init__(self, host, user_name=None, password=None, auth_from_module=False) -> None:
        self.session = requests.Session()
        if auth_from_module:
            user_name = settings.Couch.ADMIN_USER
            password = settings.Couch.ADMIN_PASSWORD
        self.__set_auth(user_name, password)
        self.host = host
    
    def prepend_host(self, *args):
        return os.path.join(self.host, *args)

    def create_db_and_user(self, db_name, user_name=None):
        if user_name is None:
            user_name = db_name

        database = self.__create_database(db_name)
        user = self.__create_db_user(db_name, user_name)
        self.__add_user_to_db(user_name, db_name)
        return database, user

    @staticmethod
    def generate_password(length=32):
        pool = string.ascii_letters + string.digits
        return ''.join([random.choice(pool) for i in range(length)])

    @staticmethod
    def check_db_name(db_name):
        valid = re.match(r'^[a-z][a-z0-9_()-]*$', db_name)
        if not valid:
            raise ValueError('The project name may only contain lower case letters and characters _, (, ), - and must start with a letter.')
        return valid

    def __set_auth(self, user_name, password):
        self.auth = (user_name, password)
        self.session.auth = self.auth

    def __create_database(self, db_name):
        db_name = db_name.lower()
        CouchDBServer.check_db_name(db_name)
            
        response = requests.put(url=self.prepend_host(db_name), auth=self.auth)
        if not response.ok:
            raise ConnectionError(response.content)
        database = CouchDatabase(self, db_name)
        return database
    
    def __create_db_user(self, db_name, user_name):
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

    def __add_user_to_db(self, user_name, db_name):
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
