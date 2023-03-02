from datetime import datetime

from app import settings
from app.field.hub import FieldHub
from app.field.database import FieldDatabase
from app.handlers.easydb_handler import EasyDBHandler


class VorgangHandler(EasyDBHandler):
    DELETED_SUFFIX = '#deleted_'

    def process_request(self, *args, **kwargs):
        if self.__is_field_project_required():
            try:
                self.__add_field_project()
            except Exception as exception:
                self.logger.error(exception)
                self.__delete_vorgang()
        return self.full_data

    def __add_field_project(self):
        identifier = self.object_data['vorgang']
        self.logger.debug(f'Creating new Field project "{identifier}"')
        self.easydb.acquire_session()
        FieldDatabase.check_database_name(identifier)
        password = self.__create_field_project(identifier)
        self.__create_easydb_object(identifier, password)

    def __is_field_project_required(self):
        if VorgangHandler.DELETED_SUFFIX in self.object_data['vorgang']:
            return False
        if self.easydb.get_object_by_field_value('field_datenbank', 'db_name', self.object_data['vorgang']) != None:
            return False
        ancestors = self.object_data['lk_vorgang_kategorie']['conceptAncestors']
        return settings.VorgangHandler.DANTE_PARENT_CONCEPT_ID in ancestors

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

    def __delete_vorgang(self):
        self.object_data['vorgang'] = self.__get_vorgang_name_with_deleted_suffix()
        tags = [{ '_id': settings.VorgangHandler.DELETED_TAG_ID }]
        self.easydb.update_object('vorgang', self.object_data['_id'], self.object_data, tags)

    def __get_vorgang_name_with_deleted_suffix(self):
        timestamp = datetime.utcnow().isoformat()
        return self.object_data['vorgang'] + VorgangHandler.DELETED_SUFFIX + timestamp
