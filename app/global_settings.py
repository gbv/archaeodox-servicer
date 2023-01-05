class Easydb:
    HOST_URL = "http://easydb-webfrontend"
    FIELD_DB_NAME_PATH = ""
    FIELD_DB_PASSWORD_PATH = ""
    FIELD_IMPORT_FILE_OBJECT_NAME = 'field_project'
    FIELD_IMPORT_MEDIA_FIELD = 'project_dump'
    IMPORT_REGISTRATION_MESSAGE = 'Import eingereicht'
    IMPORT_INITIATION_MESSAGE = 'Import begonnen'
    IMPORT_FAILURE_MESSAGE = 'Import fehlgeschlagen'
    
    IMPORT_RESULT_FIELD = 'import_result'
    IMPORT_STATE_PATH = '_mask/_tags'
    IMPORT_READY_TAG_ID = 10
    IMPORT_SUCCESSFUL_TAG_ID = 7
    IMPORT_FAILED_TAG_ID = 9
    IMPORT_HANDLING_REQUIRED_TAG_ID = 8
    

class Couch:
    HOST_URL = "http://esx-80.gbv.de:5984"

class FieldHub:
    MEDIA_URL = "http://esx-80.gbv.de:4001/files"

class GeometryParser:
    FIND_SECTION_ID_TEMPLATE = "BA {strat_unit}.{exca_int}"
    CONVERSION_URL = "http://127.0.0.1:5000/geojson"
    PROPERTY_MAP = {'info': 'shortDescription',
                    'strat_unit': 'relations.isChildOf'}