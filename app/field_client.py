import csv, json, mimetypes, requests
from uuid import uuid4

from .couch import CouchClient
from dpath import util as dp
from PIL import Image


class FieldClient(CouchClient):
    OBJECT_TYPES = ['Feature',
                'Befundanschnitt',
                'Befundkomplex',
                'Profile',
                'Find',
                'Planum',
                'Place',
                'Project',
                'Sample',
                'Trench',
                'Drawing',
                'Photo']

    def __init__(self, host, database, user_name=None, password=None, auth_from_env=False) -> None:
        super().__init__(host, user_name, password, auth_from_env)
        self.database = database

    def has_database(self, database_name):
        self.database == database_name

    @staticmethod
    def inflate(row):
        nested_keys = list(filter(lambda k: '.' in k, row.keys()))
        for key in nested_keys:
            dp.new(row, key, row[key], separator='.')
            row.pop(key)
        return row

    @staticmethod
    def remove_empties(row):
        sanitized = {}
        for key, value in row.items():
            if value:
                sanitized[key] = value
        return sanitized
      
    @staticmethod          
    def process(row):
        row = FieldClient.remove_empties(row)
        return FieldClient.inflate(row)


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

   
    def upload_image(self, image_file_name):
        identifier = self.get_or_create_id(image_file_name)
        image = Image.open(image_file_name)
        width, height = image.size
        meta_data = self.database[identifier]
        resource = meta_data['resource']
        resource['width'] = width
        resource['height'] = height
        resource['originalFilename'] = image_file_name
        
        mimetype, encoding = mimetypes.guess_type(image_file_name)
        if mimetype is None:
            return
        headers = {'Content-type': mimetype}
        params = {'type': 'original_image'}
        target_url = self.media_url + identifier
        
        response = requests.put(target_url,
                                headers=headers,
                                params=params,
                                auth=self.auth,
                                data=open(image_file_name, 'rb'))
        if response.ok:
            self.database[identifier] = meta_data

