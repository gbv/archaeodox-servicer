import json, requests

from app import settings


class DanteDatabase:
    def __init__(self, url):
        self.url = url

    def get(self, vocabulary_name, concept_id):
        url = self.url + '/data'
        params = {
            'uri': f'{settings.Dante.VOCABULARY_URI_BASE}/{vocabulary_name}/{concept_id}'
        }

        response = requests.get(url, params)
        if response.status_code == 200:
            result = json.loads(response.content)
            if len(result) == 1:
                return result[0]
            else:
                return None
        else:
            raise ValueError(f'{response.status_code}: {response.text}')

    def search(self, vocabulary_name, query):
        url = self.url + '/search'
        params = {
            'voc': vocabulary_name,
            'query': query,
            'limit': 1000,
            'properties': '-',
            'cache': 0
        }

        response = requests.get(url, params)
        if response.status_code == 200:
            result = json.loads(response.content)
        else:
            raise ValueError(f'{response.status_code}: {response.text}')
        return result
