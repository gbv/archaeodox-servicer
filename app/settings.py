class FileImportingHandler:
    IMAGE_IMPORT_MIME_TYPES = ['image/tiff', 'image/jpeg']
    CSV_IMPORT_MIME_TYPES = ['text/csv']
    SHAPEFILE_IMPORT_MIME_TYPES = ['application/zip']
    SUCCESS_TAG_ID = 8
    FAILURE_TAG_ID = 10
    SUCCESS_MESSAGE = 'OK'
    ERROR_MISSING_CREDENTIALS_MESSAGE = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte geben Sie einen Datenbanknamen und das korrekte Passwort an.'

class EasyDB:
    HOST_URL = 'http://easydb-webfrontend'

class Dante:
    HOST_URL = 'https://api.dante.gbv.de'
    VOCABULARY_PUBLISHER = 'Archäologisches Museum Hamburg'
    
class Couch:
    HOST_URL = 'http://esx-80.gbv.de:5984'

class FieldHub:
    MEDIA_URL = 'http://esx-80.gbv.de:4001/files'
    PROJECT_URL = 'http://esx-80.gbv.de:4001/projects'
    THUMBNAIL_HEIGHT = 320
    TEMPLATE_PROJECT_NAME = 'amh-default'

class GeometryParser:
    FIND_SECTION_ID_TEMPLATE = 'BA {strat_unit}.{exca_int}'
    PROPERTY_MAP = {'info': 'shortDescription',
                    'strat_unit': 'relations.isChildOf'}