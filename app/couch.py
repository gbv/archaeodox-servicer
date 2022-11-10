import json, os, requests, string, random
from uuid import uuid4
from ntpath import join

from dpath import util as dp
import re


class Client:
    CONFIG_DOCUMENT = 'configuration'
    META_KEYS = ['_id',
                 '_rev',
                 'created',
                 'modified']

    def __init__(self, host, user_name=None, password=None, auth_from_env=False) -> None:
        if auth_from_env:
            user_name = os.getenv('COUCHDB_ADMIN_USER')
            password = os.getenv('COUCHDB_ADMIN_PASSWORD')
        self.auth = (user_name, password)
        self.host = host
            
    def get_config(self, database):
        url = os.path.join(self.host, database, Client.CONFIG_DOCUMENT)
        response = requests.get(url=url, auth=self.auth)
        if response.ok:
            return response.json()

    def inject_config(self, database, path, patch):
        config = self.get_config(database)
        dp.new(config, path, patch)
        url = self.prepend_host(database, Client.CONFIG_DOCUMENT)
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

    def create_database(self, db_name):
        db_name = db_name.lower()
        if not re.match(r'^[a-z][a-z0-9_$()+/-]*$', db_name):
            raise ValueError('The project name may only contain lower case letters and characters _, $, (, ), +, -, / and must start with a letter ')
        
        response = requests.put(url=self.prepend_host(db_name), auth=self.auth)
        if not response.ok:
            raise ConnectionError(response.content)
        return response.ok
        
    def drop_db(self, db_name):
        response = requests.delete(self.prepend_host(db_name), auth=self.auth)
        return response.ok
    
    def create_db_user(self, db_name, user_name):
        user_id = f'org.couchdb.user:{user_name}'
        user = {
            'name': user_name,
            'type': 'user',
            'roles': [],
            'password': Client.generate_password()
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
        
        self.create_database(db_name)
        user = self.create_db_user(db_name, user_name)
        self.add_user_to_db(user_name, db_name)
        return user

    def copy_config(self, source, dest):
        response = requests.get(url=self.prepend_host(source, Client.CONFIG_DOCUMENT),
                                auth=self.auth)
        if not response.ok:
            raise ConnectionError(str(response.content))
        config = json.loads(response.content.decode('utf-8'))
        
        response = self.put_doc(dest, Client.CONFIG_DOCUMENT, config)
        if not response.ok:
            raise ConnectionError(response.content.decode('utf-8'))
        return response
    
    def put_doc(self, db_name, doc_id, document, sanitize=True):
        if sanitize:
            for meta_key in Client.META_KEYS:
                document.pop(meta_key, None)
        response = requests.put(self.prepend_host(db_name, doc_id), auth=self.auth, data=json.dumps(document))
        return response

    def get_or_create_id(self, database, identifier, field='resource'):
        mango =  {'selector': {f'{field}.identifier': identifier},
                  'fields': [field, '_id']
                  }
        search_results = requests.post(self.prepend_host(database, '_find'), auth=self.auth, json=mango)
        if search_results.ok:
            documents = search_results.json()['docs']
            if documents:
                return documents[0]['_id']
            else:
                id = str(uuid4())
                document = {'resource': {'identifier': identifier, 'id': id}}
                self.put_doc(database, id, document)
                return id
        else:
            raise ValueError(search_results.json()['reason'])

        

if __name__=='__main__':
    
    couch = Client('http://esx-80.gbv.de:5984', auth_from_env=True)
    r = couch.copy_config('hh9999_1234', 'amh_test')
    print(r.content)
    
    # couch.copy_config('hh9999_1234', 'amh_test')