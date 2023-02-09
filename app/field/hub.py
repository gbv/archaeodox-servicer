import requests

from app import settings
from app import credentials
from app.couchdb.server import CouchDBServer
from app.couchdb.database import CouchDatabase
from app.dante.vocabulary import DanteVocabulary
from app.utils.get_date import get_date


class FieldHub(CouchDBServer):
    CONFIG_DOCUMENT = 'configuration'
    PROJECT_DOCUMENT_ID = 'project'
    ARCHAEODOX_VOCABULARY_URI_BASE = 'http://uri.gbv.de/terminology'
    ARCHAEODOX_VOCABULARY_NAMES = [
        'amh_material',
        'amh_datierung',
        'amh_objektbezeichnung',
        'amh_warenart'
        #'amh_befunde' Not public yet
    ]
    ARCHAEODOX_VOCABULARY_PREFIX = 'amh-default'
    
    def __init__(self, host, template_project_name, user_name=None, password=None, auth_from_module=False, logger=None) -> None:
        super().__init__(host, user_name, password, auth_from_module)
        self.template = CouchDatabase(self, template_project_name, credentials.COUCHDB_ADMIN_USER, credentials.COUCHDB_ADMIN_PASSWORD)
        self.logger = logger

    def get_config(self):
        return self.template.get_doc(FieldHub.CONFIG_DOCUMENT).json()

    def update_config(self, configuration_document):
        self.template.update_doc(FieldHub.CONFIG_DOCUMENT, configuration_document)

    def create_project(self, project_identifier):
        creation_info = requests.post(f'{settings.FieldHub.PROJECT_URL}/{project_identifier}',
                                      auth=self.auth).json()
        database = CouchDatabase(self, project_identifier)
        
        database.create_doc(FieldHub.CONFIG_DOCUMENT, self.create_configuration_document())
        project = self.create_project_document(project_identifier)
        database.create_doc(FieldHub.PROJECT_DOCUMENT_ID, project)
        return creation_info['info']['password']

    def create_configuration_document(self):
        return {
            '_id': FieldHub.CONFIG_DOCUMENT,
            'resource': self.get_config()['resource'],
            'created': {'user': 'easydb', 'date': get_date()},
            'modified': []
        }

    def create_project_document(self, project_identifier):
        return {
            '_id': FieldHub.PROJECT_DOCUMENT_ID,
            'resource': {
                'identifier': project_identifier,
                'id': FieldHub.PROJECT_DOCUMENT_ID,
                'category': 'Project',
                'relations': {}
            },
            'created': {'user': 'easydb', 'date': get_date()},
            'modified': []
        }

    def update_valuelists(self):
        configuration_document = self.get_config()
        for vocabulary_name in FieldHub.ARCHAEODOX_VOCABULARY_NAMES:
            if self.logger: self.logger.debug(f'Updating valuelist for vocabulary: {vocabulary_name}')
            vocabulary = DanteVocabulary.from_uri(f'{FieldHub.ARCHAEODOX_VOCABULARY_URI_BASE}/{vocabulary_name}/')
            field_list = vocabulary.get_field_list()
            valuelist_name = f'{FieldHub.ARCHAEODOX_VOCABULARY_PREFIX}:{vocabulary_name}'
            configuration_document['resource']['valuelists'][valuelist_name] = field_list
        self.update_config(configuration_document)
