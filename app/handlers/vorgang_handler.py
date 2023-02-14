from app import settings
from app.couchdb.server import CouchDBServer
from app.field.hub import FieldHub
from app.handlers.easydb_handler import EasyDBHandler


class VorgangHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        if self.__is_field_project_required():
            identifier = self.__create_field_project_identifier()
            self.logger.debug(f'Creating new Field project "{identifier}"')
            self.easydb.acquire_session()
            self.__validate_project_identifier(identifier)
            password = self.__create_field_project(identifier)
            self.__create_easydb_object(identifier, password)
        return self.full_data

    def __is_field_project_required(self):
        ancestors = self.object_data['lk_vorgang_kategorie']['conceptAncestors']
        # TODO Move to settings
        return '76f1f241-6425-4fd3-a93c-ee88a47affc1' in ancestors

    def __create_field_project_identifier(self):
        return self.object_data['vorgang'].lower().strip()

    def __validate_project_identifier(self, identifier):
        if self.easydb.get_item('field_datenbank', 'db_name', identifier) != None:
            raise ValueError(f'Field database "{identifier}" already exists.')
        CouchDBServer.check_db_name(identifier, True)

    def __create_field_project(self, identifier):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = hub.create_project(identifier)
        return password

    def __create_easydb_object(self, identifier, password):
        fields_data = {
            'db_name': identifier,
            'passwort': password,
            'lk_vorgang': self.inner_data
        }

        self.easydb.create_object('field_datenbank', fields_data)