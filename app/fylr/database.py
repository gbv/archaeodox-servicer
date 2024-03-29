import json, requests
from os.path import join

from app import settings
    

class Fylr:
    API_PATH = 'api/v1'

    def __init__(self, url, logger):
        self.url = url
        self.db_url = join(url, Fylr.API_PATH, 'db')
        self.logger = logger

    def acquire_access_token(self):
        url = join(self.url, 'api', 'oauth2', 'token')
        data = {
            'grant_type': 'password',
            'scope': 'offline',
            'client_id': settings.Fylr.CLIENT_ID,
            'client_secret': settings.Fylr.CLIENT_SECRET,
            'username': settings.Fylr.USER_NAME,
            'password': settings.Fylr.PASSWORD
        }
        response = requests.post(url, data=data)
        if response.status_code == 200:
            self.access_token = json.loads(response.content)['access_token']
        else:
            raise ValueError(f'Failed to acquire access token: {response.text}')

    def get_object_by_id(self, object_type, id):
        get_url = join(
            self.db_url,
            f'{object_type}/{object_type}__servicer',
            str(id)
        )
        params = {
            'access_token': self.access_token,
            'format': 'full'
        }

        response = requests.get(get_url, params=params)
        if response.status_code == 200:
            result = json.loads(response.content)[0]
        else:
            raise ValueError(f'{response.status_code}: {response.text}')
        return result

    def get_object_by_field_values(self, object_type, field_values):
        query = { 'type': 'complex', 'search': [] }
        for field_name, field_value in field_values.items():
            query['search'].append({
                'type': 'in',
                'bool': 'must',
                'fields': ['.'.join((object_type, field_name))],
                'in': [field_value]
            })
        search_result = self.__search(query)
        if search_result is not None and len(search_result) == 1:
            result_object = search_result[0]
            del result_object['_score']
            return result_object
        else:
            return None

    def changelog_search(self, object_type, from_date, to_date, operation):
        query = {
            'type': 'complex',
            'search': [
                {
                    'type': 'changelog_range',
                    'operation': operation,
                    'from': from_date,
                    'to': to_date
                },
                {
                    'type': 'in',
                    'fields': ['_objecttype'],
                    'in': [object_type]
                }
            ]
        }
        return self.__search(query)

    def create_object(self, object_type, fields_data, pool=None, tags=None):
        params = { 'access_token': self.access_token }
        data = {
            '_objecttype': object_type,
            '_mask': object_type + '__servicer'
        }
        if pool is not None:
            fields_data['_pool'] = pool
        if tags is not None:
            data['_tags'] = tags
        fields_data['_version'] = 1
        data[object_type] = fields_data

        url = join(self.db_url, object_type)
        response = requests.post(url, params=params, json=[data])
        if not response.ok:
            raise ConnectionError(response.text)
        return response.json()[0]

    def update_object(self, object_type, id, fields_data, tags=None):
        params = { 'access_token': self.access_token }
        current_object = self.get_object_by_id(object_type, id)
        current_version = current_object[object_type]['_version']
        updated_object = {
            '_mask': current_object['_mask'],
            '_objecttype': object_type
        }
        updated_object[object_type] = fields_data
        updated_object[object_type]['_version'] = current_version + 1
        if tags is not None:
            updated_object['_tags'] = tags
        else:
            updated_object['_tags'] = current_object['_tags']

        url = join(self.db_url, object_type)  
        response = requests.post(url, params=params, json=[updated_object])
        if not response.ok:
            raise ConnectionError(response.text)
        return response.ok
    
    def delete_object(self, object_type, id):
        params = { 'access_token': self.access_token, 'delete_policy': 'remove', 'confirm': 'delete' }
        current_object = self.get_object_by_id(object_type, id)
        current_version = current_object[object_type]['_version']
        
        url = join(self.db_url, object_type)
        response = requests.delete(url, params=params, json=[[id, current_version]])
        if not response.status_code == 200:
            raise ConnectionError(response.text)
        return response.ok

    def download_asset(self, url):
        response = requests.get(url + '&access_token=' + self.access_token)
        if response.ok:
            return response.content
        else:
            raise ValueError(response.text)

    def create_asset(self, filename, data, mimetype):
        params = {
            'access_token': self.access_token,
            'instance': filename
        }
        files = {
            'file': (filename, data, mimetype)
        }
        url = join(self.url, Fylr.API_PATH, 'eas', 'put')
        response = requests.post(url, params=params, files=files)
        if not response.ok:
            raise ConnectionError(response.text)
        return response.json()

    def __search(self, query):
        params = { 'access_token': self.access_token }
        url = join(self.url, Fylr.API_PATH, 'search')
        response = requests.post(url, params=params, json={ 'search': [query] })
        if response.status_code == 200:
            return json.loads(response.content)['objects']
        else:
            self.logger.error(response)
            return None
