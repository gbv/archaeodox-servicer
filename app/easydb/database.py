import json, requests
from os.path import join

from app import settings
    

class EasyDB:
    API_PATH = 'api/v1'

    def __init__(self, url, logger):
        self.url = url
        self.session_url = join(url, EasyDB.API_PATH, 'user', 'session')
        self.search_url = join(url, EasyDB.API_PATH, 'search')
        self.session_auth_url = join(url, EasyDB.API_PATH, 'session', 'authenticate')
        self.db_url = join(url, EasyDB.API_PATH, 'db')
        self.objects_url = join(url, EasyDB.API_PATH, 'objects')
        self.create_asset_url = join(url, EasyDB.API_PATH, 'eas', 'rput')
        self.logger = logger

    def acquire_access_token(self):
        url = join(self.url, 'api', 'oauth2', 'token')
        data = {
            'grant_type': 'password',
            'scope': 'offline',
            'client_id': settings.EasyDB.CLIENT_ID,
            'client_secret': settings.EasyDB.CLIENT_SECRET,
            'username': settings.EasyDB.USER_NAME,
            'password': settings.EasyDB.PASSWORD
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.access_token = json.loads(response.content)['access_token']
        else:
            raise ValueError(f'Failed to acquire access token: {response.text}')

    def get_object_by_id(self, object_type, id):
        get_url = join(
            self.db_url,
            f'{object_type}/{object_type}__all_fields/',
            str(id)
        )
        params = {
            'access_token': self.access_token,
            'format': 'long'
        }

        response = requests.get(get_url, params=params)
        if response.status_code == 200:
            result = json.loads(response.content)[0]
        else:
            raise ValueError(f'{response.status_code}: {response.text}')
        return result

    def get_object_by_field_value(self, object_type, field_name, field_value):
        search_result = self.search(object_type, field_name, field_value)
        if search_result is not None and len(search_result) == 1:
            return search_result[0]
        else:
            return None

    def search(self, object_type, field_name, field_value):
        query = {
            'type': 'in',
            'bool': 'must',
            'fields': ['.'.join((object_type, field_name))],
            'in': [field_value]
        }
        params = { 'access_token': self.access_token }

        response = requests.post(self.search_url, params=params, json={ 'search': [query] })
        if response.status_code == 200:
            return json.loads(response.content)['objects']
        else:
            return None

    def create_object(self, object_type, fields_data, pool=None, tags=None):
        params = { 'access_token': self.access_token }
        data = { '_mask': object_type + '__all_fields' }
        if pool is not None:
            fields_data['_pool'] = pool
        if tags is not None:
            data['_tags'] = tags
        fields_data['_version'] = 1
        data[object_type] = fields_data

        insert_url = join(self.db_url, object_type)
        response = requests.put(insert_url, params=params, json=[data])
        if not response.ok:
            raise ConnectionError(response.text)
        return response.ok

    def update_object(self, object_type, id, fields_data, tags=None):
        params = { 'access_token': self.access_token }
        current_object = self.get_object_by_id(object_type, id)
        current_version = current_object[object_type]['_version']
        current_object[object_type] = fields_data
        current_object[object_type]['_version'] = current_version + 1
        if tags is not None:
            current_object['_tags'] = tags

        update_url = join(self.db_url, object_type)  
        response = requests.post(update_url, params=params, json=[current_object])
        if not response.ok:
            raise ConnectionError(response.text)
        return response.ok

    def create_asset_from_url(self, filename, url):
        params = {
            'access_token': self.access_token,
            'filename': filename,
            'url': url
        }

        response = requests.post(self.create_asset_url, params=params)
        if not response.ok:
            raise ConnectionError(response.text)
        return response.json()
