from datetime import datetime

from app import settings
from app.field.hub import FieldHub
from app.field.database import FieldDatabase
from app.handlers.fylr_handler import FylrHandler


class VorgangHandler(FylrHandler):
    DELETED_SUFFIX = '#deleted_'

    def process_request(self, *args, **kwargs):
        self.fylr.acquire_access_token()
        if self.__is_field_project_required():
            try:
                self.__add_field_project()
            except Exception as exception:
                self.logger.error(exception, exc_info=True)
                self.__delete_vorgang()
        return

    def __add_field_project(self):
        identifier = self.object_data['vorgang']
        self.logger.debug(f'Creating new Field project "{identifier}"')
        self.fylr.acquire_access_token()
        self.__validate_project_identifier(identifier)
        password = self.__create_field_project(identifier)
        self.__create_fylr_object(identifier, password)

    def __is_field_project_required(self):
        if VorgangHandler.DELETED_SUFFIX in self.object_data['vorgang']:
            return False
        ancestors = self.object_data['lk_vorgang_kategorie']['conceptAncestors']
        return settings.VorgangHandler.DANTE_PARENT_CONCEPT_ID in ancestors

    def __validate_project_identifier(self, identifier):
        if identifier is None or len(identifier) == 0:
            raise ValueError('Field "vorgang" has to be filled out')
        if self.fylr.get_object_by_field_values('field_datenbank', { 'db_name': identifier }) != None:
            raise ValueError(f'Field database "{identifier}" already exists.')
        FieldDatabase.check_database_name(identifier)

    def __create_field_project(self, identifier):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = hub.create_project(identifier)
        return password

    def __create_fylr_object(self, identifier, password):
        fields_data = {
            'db_name': identifier,
            'passwort': password,
            'lk_vorgang': {
                '_objecttype': 'vorgang',
                '_mask': 'vorgang__servicer',
                'vorgang': {
                    '_id': self.object_data['_id'] 
                }
            }
        }

        self.fylr.create_object('field_datenbank', fields_data)

    def __delete_vorgang(self):
        self.object_data['vorgang'] = self.__get_vorgang_name_with_deleted_suffix()
        tags = [{ '_id': settings.VorgangHandler.DELETED_TAG }]
        self.fylr.update_object('vorgang', self.object_data['_id'], self.object_data, tags)
    
    def __get_vorgang_name_with_deleted_suffix(self):
        timestamp = datetime.utcnow().isoformat()
        return self.object_data['vorgang'] + VorgangHandler.DELETED_SUFFIX + timestamp
