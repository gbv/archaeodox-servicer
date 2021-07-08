import json, requests
from os.path import join as path_join


class EasydbClient:
    API_PATH = "api/v1"

    def __init__(self, url, session_token):
        self.url = url
        self.token = session_token
        self.session_url = path_join(url,
                                     EasydbClient.API_PATH,
                                     "session")
        self.search_url = path_join(url,
                                    EasydbClient.API_PATH,
                                    "search")

    def get_item(self, item_type, id, id_field="_id", pretty=0):
        search = {"type": "in",
                  "bool": "must",
                  "fields": [".".join((type, id_field))],
                  "in": id
                  }
        data = {"token": self.token,
                  "pretty": 0,
                  "search": search}
        response = requests.post(self.search_url,
                                 data=data)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            return None
