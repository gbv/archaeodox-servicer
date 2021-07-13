import json, requests
from os.path import join as path_join
import credentials


class EasydbClient:
    API_PATH = "api/v1"

    def __init__(self, url):
        self.url = url
        self.session_url = path_join(url,
                                     EasydbClient.API_PATH,
                                     "session")
        self.search_url = path_join(url,
                                    EasydbClient.API_PATH,
                                    "search")
        self.session_auth_url = path_join(url,
                                          EasydbClient.API_PATH,
                                          "session",
                                          "authenticate")
        self.acquire_session()

    def acquire_session(self):
        session_response = requests.get(self.session_url)
        if session_response.status_code == 200:
            session_info = json.loads(session_response.content)
            self.session_token = session_info['token']

            params = {"token": self.session_token,
                      "login": credentials.USER_NAME,
                      "password": credentials.PASSWORD}
            auth_response = requests.post(self.session_auth_url,
                                          params=params)
            if not auth_response.status_code == 200:
                raise ValueError(f"Failed to authenticate: {auth_response.content}")
        else:
            raise ValueError(f"Failed to acquire session from {self.session_url}")

    def get_item(self, item_type, id, id_field="_id", pretty=0):
        search = {"type": "in",
                  "bool": "must",
                  "fields": [".".join((item_type, id_field))],
                  "in": id
                  }
        data = {"token": self.token,
                  "pretty": 0,
                  "search": search}
        headers = {"Content-Type": "text/json"}
        response = requests.post(self.search_url,
                                 headers=headers,
                                 data=data)

        return response.status_code, json.loads(response.content)
