import json, os, requests


class CouchDatabase:
    META_KEYS = ['_rev']

    def __init__(self, server, name, user_name=None, password=None):
        self.server = server
        if not server.has_database(name):
            server.create_database(name)
        self.session = requests.Session()
        self.set_auth(user_name, password)
        self.name = name
        self.url = server.prepend_host(name)
        self.search_url = server.prepend_host(name, '_find')

    def set_auth(self, user_name, password):
        if user_name is None:
            self.auth = self.server.auth
        else:
            self.auth = (user_name, password)
        self.session.auth = self.auth

    def create_doc(self, doc_id, document):
        response = self.session.put(os.path.join(self.url, doc_id), data=json.dumps(document))
        return response

    def update_doc(self, doc_id, document):
        if not 'created' in document.keys():
            raise ValueError(f"Document has never been created: {document}")
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

    def get_all_ids(self):
        response = self.session.get(f"{self.url}/_all_docs", auth=self.auth)
        if response.ok:
            rows = response.json()['rows']
            ids = [row['id'] for row in rows]
            return ids
