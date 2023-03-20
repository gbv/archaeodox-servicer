import requests

from app import settings
from app.couchdb.server import CouchDBServer
from app.couchdb.database import CouchDatabase
from app.dante.vocabulary import DanteVocabulary
from app.field import document_utility


class FieldHub(CouchDBServer):
    CONFIG_DOCUMENT = 'configuration'
    PROJECT_DOCUMENT_ID = 'project'
    
    def __init__(self, host, template_project_name, user_name=None, password=None, auth_from_module=False, logger=None):
        super().__init__(host, user_name, password, auth_from_module)
        self.template_project = CouchDatabase(
            self, template_project_name, settings.Couch.ADMIN_USER, settings.Couch.ADMIN_PASSWORD
        )
        self.logger = logger

    def create_project(self, project_identifier):
        creation_info = requests.post(f'{settings.FieldHub.PROJECT_URL}/{project_identifier}',
                                      auth=self.auth).json()
        database = CouchDatabase(self, project_identifier)
        
        database.create_document(FieldHub.CONFIG_DOCUMENT, self.create_configuration_document())
        project = self.create_project_document(project_identifier)
        database.create_document(FieldHub.PROJECT_DOCUMENT_ID, project)
        return creation_info['info']['password']

    def create_configuration_document(self):
        return document_utility.get_document(
            FieldHub.CONFIG_DOCUMENT,
            self.__get_configuration_template()['resource']
        )

    def create_project_document(self, project_identifier):
        resource = {
            'identifier': project_identifier,
            'id': FieldHub.PROJECT_DOCUMENT_ID,
            'category': 'Project',
            'relations': {}
        }
        return document_utility.get_document(FieldHub.PROJECT_DOCUMENT_ID, resource)

    def __get_configuration_template(self):
        return self.template_project.get_document(FieldHub.CONFIG_DOCUMENT).json()
