from app import settings
from app.field.hub import FieldHub
from app.field.database import FieldDatabase
from app.dante.vocabulary import DanteVocabulary


def update(logger):
    field_hub = FieldHub(settings.Couch.HOST_URL,
                settings.FieldHub.TEMPLATE_PROJECT_NAME,
                auth_from_module=True,
                logger=logger)

    database = FieldDatabase(
        field_hub,
        settings.ValuelistsUpdater.VALUELISTS_PROJECT_NAME,
        settings.Couch.ADMIN_USER,
        settings.Couch.ADMIN_PASSWORD
    )
    configuration_document = database.get_document('configuration')

    for vocabulary_name in settings.Dante.VOCABULARY_NAMES:
        if logger: logger.debug(f'Updating valuelist for vocabulary: {vocabulary_name}')
        vocabulary = DanteVocabulary.from_uri(f'{settings.Dante.VOCABULARY_URI_BASE}/{vocabulary_name}/')
        field_list = vocabulary.get_field_list()
        valuelist_name = f'{settings.Dante.VOCABULARY_PREFIX}:{vocabulary_name}'
        configuration_document['resource']['valuelists'][valuelist_name] = field_list

    database.update_document('configuration', configuration_document)
