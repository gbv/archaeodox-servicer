import json, requests
from os.path import join

from app import credentials
    

class EasyDB:
    API_PATH = 'api/v1'

    def __init__(self, url, logger):
        self.url = url
        self.session_url = join(url, EasyDB.API_PATH, 'session')
        self.search_url = join(url, EasyDB.API_PATH, 'search')
        self.session_auth_url = join(url, EasyDB.API_PATH, 'session', 'authenticate')
        self.db_url = join(url, EasyDB.API_PATH, 'db')
        self.objects_url = join(url, EasyDB.API_PATH, 'objects')
        self.create_asset_url = join(url, EasyDB.API_PATH, 'eas', 'rput')
        self.logger = logger

    def acquire_session(self):
        session_response = requests.get(self.session_url)
        if session_response.status_code == 200:
            session_info = json.loads(session_response.content)
            self.session_token = session_info['token']

            params = {'token': self.session_token,
                      'login': credentials.EASYDB_USER_NAME,
                      'password': credentials.EASYDB_PASSWORD}
            auth_response = requests.post(self.session_auth_url,
                                          params=params)
            self.logger.debug(f'Attempting auth.')
            if not auth_response.status_code == 200:
                raise ValueError(f'Failed to authenticate: {auth_response.text}')
        else:
            raise ValueError(f'Failed to acquire session from {self.session_url}')

    def get_object_by_field_value(self, object_type, field_name, field_value):
        search_result = self.search(object_type, field_name, field_value)
        self.logger.debug('Search result:')
        self.logger.debug(search_result)
        if search_result is not None and len(search_result) == 1:
            return search_result[0]
        else:
            return None

    def search(self, item_type, field_name, field_value):
        query = {
            'type': 'in',
            'bool': 'must',
            'fields': ['.'.join((item_type, field_name))],
            'in': [field_value]
        }
        params = { 'token': self.session_token }
        response = requests.post(self.search_url, params=params, json={ 'search': [query] })

        if response.status_code == 200:
            return json.loads(response.content)['objects']
        else:
            return None

    def get_tags(self, token=None):
        tags_url = join(self.url,
                        EasyDB.API_PATH,
                        'tags')
        params = {'token': token if token is not None else self.session_token}
        return requests.get(tags_url, params=params).json()

    def get_by_global_id(self, id, version='latest', token=None):
        get_url = f'{self.objects_url}/id/{id}/{version}'
        params = {'token': token if token is not None else self.session_token}
        params['format'] = 'long'

        response = requests.get(get_url, params=params)

        if response.status_code == 200:
            return json.loads(response.content)
        else:
            raise ValueError(f'{response.status_code}: {response.text}')

    def get_object_by_id(self, item_type, id, token=None):
        get_url = join(self.db_url,
                       f'{item_type}/{item_type}__all_fields/',
                       str(id))
        params = {'token': token if token is not None else self.session_token}
        params['format'] = 'long'

        response = requests.get(get_url, params=params)

        if response.status_code == 200:
            result = json.loads(response.content)[0]
        else:
            raise ValueError(f'{response.status_code}: {response.text}')
        return result

    def update_item(self, item_type, id, token=None):
        latest = self.get_object_by_id(item_type=item_type, id=id, token=token)
        current_version = latest[item_type]['_version']
        latest[item_type]['_version'] = current_version + 1
        for k, v in up_data.items():
            latest[item_type][k] = v
        update_url = join(self.db_url,
                          item_type)
        params = {'token': token if token is not None else self.session_token}
        response = requests.post(update_url, json=[latest], params=params)
        if not response.ok:
            raise ConnectionError(response.text)
        return response.ok

    def create_object(self, object_type, fields_data, pool=None, tags=None, token=None):
        params = { 'token': token if token is not None else self.session_token }
        data = { '_mask': object_type + '_anlage' }
        if pool is not None:
            fields_data['_pool'] = pool
        if tags is not None:
            data['_tags'] = tags
        fields_data['_version'] = 1
        data[object_type] = fields_data
        insert_url = join(self.db_url,
                          object_type)
        response = requests.put(insert_url, params=params, json=[data])
        if not response.ok:
            raise ConnectionError(response.text)
        return response.ok

    def create_asset_from_url(self, filename, url):
        params = {
            'token': self.session_token,
            'filename': filename,
            'url': url
        }
        response = requests.post(self.create_asset_url, params=params)
        if not response.ok:
            raise ConnectionError(response.text)
        return response.json()
