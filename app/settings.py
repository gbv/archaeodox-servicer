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
    TEMPLATE_PROJECT_NAME = 'amh-default'

class FileImportingHandler:
    IMAGE_IMPORT_MIME_TYPES = ['image/tiff', 'image/jpeg']
    CSV_IMPORT_MIME_TYPES = ['text/csv']
    SHAPEFILE_IMPORT_MIME_TYPES = ['application/zip']
    SUCCESS_TAG_ID = 8
    FAILURE_TAG_ID = 10

class ImageImporter:
    THUMBNAIL_HEIGHT = 320
    THUMBNAIL_JPEG_QUALITY = 60

class CSVImporter:
    ALLOWED_CATEGORIES = ['Project', 'Place', 'Trench', 'FeatureGroup', 'Feature', 'FeatureSegment', 'Find', 'Sample',
        'Image', 'Photo', 'Amh-default:PlanDrawing', 'Amh-default:FindDrawing', 'Planum', 'Profile']

class ShapefileImporter:
    FIND_SECTION_ID_TEMPLATE = 'BA {strat_unit}.{exca_int}'
    PROPERTY_MAP = {'info': 'shortDescription',
                    'strat_unit': 'relations.isChildOf'}
