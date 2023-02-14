import requests
from uuid import uuid4

from app import settings
from app.couchdb.database import CouchDatabase
from app.utils.get_date import get_date


class FieldDatabase(CouchDatabase):
    OBJECT_TYPES = ['Feature',
                    'Befundanschnitt',
                    'Befundkomplex',
                    'Find',
                    'Planum',
                    'Place',
                    'Project',
                    'Sample',
                    'Trench',
                    'Drawing',
                    'Photo',
                    'Profile']

    def __init__(self, server, name, password):
        super().__init__(server, name, name, password)
        self.media_url = f'{settings.FieldHub.MEDIA_URL}/{self.name}/'

    def get_or_create_document(self, identifier):
        mango = {'selector': {f'resource.identifier': identifier}}
        search_results = self.session.post(self.search_url, json=mango)
        if search_results.ok:
            documents = search_results.json()['docs']
            if documents:
                return documents[0]
            else:
                id = str(uuid4())
                document = {'_id': id,
                            'resource': {
                                'identifier': identifier,
                                'id': id,
                                'relations': {}
                            },
                            'created':{'user':'easydb', 'date': get_date()},
                            'modified':[]}
                response = self.create_doc(id, document)
                document['_rev'] = response.json()['rev']
                return document
        else:
            raise ValueError(search_results.json()['reason'])
        
    def upload_image(self, id, image_data, mimetype, image_type):
        target_url = self.media_url + id
        params = { 'type': image_type }
        headers = { 'Content-type': mimetype }
        with image_data:
            return requests.put(
                target_url,
                headers=headers,
                params=params,
                auth=self.auth,
                data=image_data.getvalue()
            )

    def populate_resource(self, resource_data, resource_type):
        identifier = resource_data['identifier']
        document = self.get_or_create_document(identifier)
        id = document['_id']
        
        resource_data['id'] = id
        resource_data['type'] = resource_type
        relations = resource_data.get('relations', {})
        for relation, target in relations.items():
            target_identifiers = target.split(';')
            target_ids = [self.get_or_create_document(identifier)['_id'] for identifier in target_identifiers]
            resource_data['relations'][relation] = target_ids
            
        document['resource'] = resource_data
        return self.update_doc(id, document=document)
