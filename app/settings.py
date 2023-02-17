class EasyDB:
    HOST_URL = 'http://easydb-webfrontend'

class Dante:
    HOST_URL = 'https://api.dante.gbv.de'
    VOCABULARY_PUBLISHER = 'Archäologisches Museum Hamburg'
    VOCABULARY_URI_BASE = 'http://uri.gbv.de/terminology'
    VOCABULARY_NAMES = [
        'amh_material',
        'amh_datierung',
        'amh_objektbezeichnung',
        'amh_warenart',
        'amh_befunde'
    ]
    VOCABULARY_PREFIX = 'amh-default'
    
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

class FileImport:
    FORMATS = {
        'csv': { 'file_type': 'csv', 'expected_format': 'csv', 'importer': 'csv' },
        'jpg': { 'file_type': 'jpeg', 'expected_format': 'jpg', 'importer': 'image' },
        'jpeg': { 'file_type': 'jpeg', 'expected_format': 'jpg', 'importer': 'image' },
        'tif': { 'file_type': 'tiff', 'expected_format': 'tif', 'importer': 'image' },
        'tiff': { 'file_type': 'tiff', 'expected_format': 'tif', 'importer': 'image' },
        'zip': { 'file_type': 'zip', 'expected_format': 'zip', 'importer': 'shapefile' }
    }
    SUCCESS_TAG_ID = 8
    FAILURE_TAG_ID = 10

class ImageImporter:
    THUMBNAIL_HEIGHT = 320
    THUMBNAIL_JPEG_QUALITY = 60

class CSVImporter:
    ALLOWED_CATEGORIES = ['Project', 'Place', 'Trench', 'FeatureGroup', 'Feature', 'FeatureSegment', 'Find', 'Sample',
        'Image', 'Photo', 'Amh-default:PlanDrawing', 'Amh-default:FindDrawing', 'Planum', 'Profile']
