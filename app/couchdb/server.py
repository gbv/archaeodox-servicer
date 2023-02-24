import requests

from app import settings


class CouchDBServer:
    def __init__(self, url, user_name=None, password=None, auth_from_module=False):
        self.session = requests.Session()
        if auth_from_module:
            user_name = settings.Couch.ADMIN_USER
            password = settings.Couch.ADMIN_PASSWORD
        self.__set_auth(user_name, password)
        self.url = url

    def __set_auth(self, user_name, password):
        self.auth = (user_name, password)
        self.session.auth = self.auth
