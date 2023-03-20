import requests, re
from uuid import uuid4

from app import settings
from app.couchdb.database import CouchDatabase
from app.field import document_utility


class FieldDatabase(CouchDatabase):
    def __init__(self, server, name, user_name, password):
        super().__init__(server, name, user_name, password)
        self.media_url = f'{settings.FieldHub.MEDIA_URL}/{self.name}/'

    def get_or_create_document(self, identifier, category=None):
        documents = self.search({ 'selector': { 'resource.identifier': identifier } })
        if documents is not None and len(documents) > 0:
            return documents[0]
        else:
            id = str(uuid4())
            document = self.__get_empty_document(id, identifier, category)
            response = self.create_document(id, document)
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

    def populate_resource(self, resource_data, identifier=None):
        if identifier is None:
            identifier = resource_data['identifier']
        document = self.get_or_create_document(identifier)

        for key in resource_data:
            if key not in ['relations', 'id']:
                document['resource'][key] = resource_data[key]

        relations = resource_data.get('relations', {})
        for relation_name, target_ids in relations.items():
            document['resource']['relations'][relation_name] = target_ids
    
        response = self.update_document(document['_id'], document=document)
        document['_rev'] = response.json()['rev']
        return document

    @staticmethod
    def check_database_name(name):
        valid = re.match(r'^[a-z][a-z0-9_-]{0,27}$', name)
        if not valid:
            raise ValueError('The project name may only contain lower case letters and characters _, (, ), - and must start with a letter.')
        return valid

    def __get_empty_document(self, id, identifier, category):
        resource = {
            'identifier': identifier,
            'id': id,
            'relations': {}
        }
        if category is not None:
            resource['category'] = category
        
        return document_utility.get_document(id, resource)
