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

class Couch:
    HOST_URL = "http://esx-80.gbv.de:5984"

class FieldHub:
    MEDIA_URL = "http://esx-80.gbv.de:4001/files"