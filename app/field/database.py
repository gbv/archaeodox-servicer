import requests
from uuid import uuid4

from app import settings
from app.couchdb.database import CouchDatabase
from app.utils.get_date import get_date


class FieldDatabase(CouchDatabase):
    def __init__(self, server, name, password):
        super().__init__(server, name, name, password)
        self.media_url = f'{settings.FieldHub.MEDIA_URL}/{self.name}/'

    def get_or_create_document(self, identifier, category=None):
        documents = self.search({ 'selector': { 'resource.identifier': identifier } })
        if documents and len(documents) > 0:
            return documents[0]
        else:
            id = str(uuid4())
            document = self.__get_empty_document(id, identifier, category)
            response = self.create_doc(id, document)
            document['_rev'] = response.json()['rev']
            return document

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

    def populate_resource(self, resource_data):
        identifier = resource_data['identifier']
        document = self.get_or_create_document(identifier)

        for key in resource_data:
            if key not in ['relations', 'id']:
                document['resource'][key] = resource_data[key]

        relations = resource_data.get('relations', {})
        for relation_name, target_ids in relations.items():
            document['resource']['relations'][relation_name] = target_ids
    
        response = self.update_doc(document['_id'], document=document)
        document['_rev'] = response.json()['rev']
        return document


    def __get_empty_document(self, id, identifier, category):
        document = {
            '_id': id,
            'resource': {
                'identifier': identifier,
                'id': id,
                'relations': {}
            },
            'created': {
                'user': 'easydb',
                'date': get_date()
            },
            'modified': []
        }
        if category is not None:
            document['resource']['category'] = category
        
        return document
