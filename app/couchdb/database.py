import json, requests


class CouchDatabase:
    def __init__(self, server, name, user_name=None, password=None):
        self.server = server
        self.session = requests.Session()
        self.__set_auth(user_name, password)
        self.name = name
        self.url = '/'.join(server.url, name)
        self.search_url = '/'.join(self.url, '_find')

    def create_doc(self, doc_id, document):
        response = self.session.put('/'.join(self.url, doc_id), data=json.dumps(document))
        return response

    def update_doc(self, doc_id, document):
        if not 'created' in document.keys():
            raise ValueError(f'Document has never been created: {document}')
        existing = self.get_doc(doc_id).json()
        try:
            current_revision = existing['_rev']
        except:
            print(doc_id)
            print(document)
            raise
        return self.session.put(f'{self.url}/{doc_id}',
                                params={'rev': current_revision},
                                data=json.dumps(document))

    def get_doc(self, doc_id):
        return self.session.get(f'{self.url}/{doc_id}')

    def search(self, query):
        response = self.session.post(self.search_url, json=query)
        if response.ok:
            return response.json()['docs']
        else:
            raise ValueError(response.json()['reason'])

    def __set_auth(self, user_name, password):
        if user_name is None:
            self.auth = self.server.auth
        else:
            self.auth = (user_name, password)
        self.session.auth = self.auth
