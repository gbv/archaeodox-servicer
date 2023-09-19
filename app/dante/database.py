import json, requests


class DanteDatabase:
    def __init__(self, url):
        self.url = url

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
