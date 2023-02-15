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

class VorgangHandler:
    PROJECT_IDENTIFIER_PREFIX = 'hh'
    # If a child concept of this concept is selected in field 'lk_vorgang_kategorie' of the Vorgang object,
    # a new Field database is created.
    DANTE_PARENT_CONCEPT_ID = '76f1f241-6425-4fd3-a93c-ee88a47affc1'

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
