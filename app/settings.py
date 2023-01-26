class EdbHandlers:
    IMAGE_IMPORT_MIME_TYPES = ["image/tiff", "image/jpeg"]
    CSV_IMPORT_MIME_TYPES = ["text/csv"]
    SHAPEFILE_IMPORT_MIME_TYPES = ["application/zip"]

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
    PROJECT_URL = "http://esx-80.gbv.de:4001/projects"
    THUMBNAIL_HEIGHT = 320
    TEMPLATE_PROJECT_NAME = 'hh9999_12345'

class GeometryParser:
    FIND_SECTION_ID_TEMPLATE = "BA {strat_unit}.{exca_int}"
    CONVERSION_URL = "http://127.0.0.1:5000/geojson"
    PROPERTY_MAP = {'info': 'shortDescription',
                    'strat_unit': 'relations.isChildOf'}

class WFS:
    OBJECT_TYPE = "teller"
    OBJECT_NAMESPACE = "hekate"
    GEO_SERVER_URL = "https://geodienste.gbv.de/nld/hekate/wfs"
    GEOMETRY = "found_at"
    ATTRIBUTES = ["text", ]

    RETURN = "feature_id"
    CONVERSION_URL = "http://converter:5000/gml/"

    TRANSACTION_ATTRIBUTES = {"version": "1.1.0",
                            "service": "WFS",
                            "xmlns": "http://geodienste.gbv.de/nld/hekate/",
                            "xmlns:" + OBJECT_NAMESPACE: OBJECT_NAMESPACE,
                            "xmlns:gml": "http://www.opengis.net/gml",
                            "xmlns:ogc": "http://www.opengis.net/ogc",
                            "xmlns:wfs": "http://www.opengis.net/wfs",
                            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "xsi:schemaLocation": """http://geodienste.gbv.de/nld/hekate/
                                                    http://www.opengis.net/wfs
                                                    ../wfs/1.1.0/WFS.xsd"""
                            }
