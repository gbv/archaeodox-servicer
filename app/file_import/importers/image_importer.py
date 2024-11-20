import mimetypes, io, re
from os.path import basename
from PIL import Image
from geotiff import GeoTiff

from app import settings, messages


def run(image_data, image_file_name, document_type_code, has_worldfile, georeferenced, field_database):
    planum_or_profile_identifier = __get_planum_or_profile_identifier(image_file_name)

    image_object = io.BytesIO(image_data)
    image = Image.open(io.BytesIO(image_object.getvalue()))
    width, height = image.size

    mimetype, _ = mimetypes.guess_type(image_file_name)
    georeference = None
    if mimetype == 'image/tiff':
        georeference = __get_georeference(image_object, width, height)
    if not georeference and not has_worldfile and georeferenced:
        raise ValueError(messages.FileImport.ERROR_MISSING_GEOREFERENCE)

    image_document = __create_image_document(field_database, image_file_name, document_type_code, width, height, georeference)
    id = image_document['_id']
    format = basename(mimetype)
    
    response = field_database.upload_image(id, __get_image_bytes(image, format), mimetype, 'original_image')
    if response.ok:
        field_database.upload_image(id, __generate_thumbnail(image), mimetype, 'thumbnail_image')
    else:
        raise ConnectionError(response.content)

    if planum_or_profile_identifier is not None:
        __set_relations(image_document, planum_or_profile_identifier, georeferenced, field_database)

def __get_planum_or_profile_identifier(image_file_name):
    planum_prefix = settings.FileImport.CATEGORY_PREFIXES['Planum']
    profile_prefix = settings.FileImport.CATEGORY_PREFIXES['Profile']
    match = re.search(r'(' + planum_prefix + r'|' + profile_prefix + r')\d+', image_file_name)
    if match is not None:
        return match[0]
    else:
        return None

def __create_image_document(field_database, image_file_name, document_type_code, width, height, georeference):
    image_document = field_database.get_or_create_document(image_file_name)
    resource = image_document['resource']
    resource['category'] = settings.ImageImporter.CATEGORIES[document_type_code]
    resource['width'] = width
    resource['height'] = height
    resource['originalFilename'] = image_file_name
    if georeference is not None:
        resource['georeference'] = georeference
    if 'relations' not in resource:
        resource['relations'] = {}
    return image_document

def __set_relations(image_document, planum_or_profile_identifier, georeferenced, field_database):
    planum_or_profile_document = field_database.get_or_create_document(planum_or_profile_identifier)
    __link_with_profile_or_planum(image_document, planum_or_profile_document)
    field_database.update_document(planum_or_profile_document['resource']['id'], planum_or_profile_document)
    field_database.update_document(image_document['resource']['id'], image_document)
    if georeferenced:
        project_document = field_database.get_or_create_document(field_database.name)
        __set_as_map_layer(image_document, project_document)
        field_database.update_document('project', project_document)

def __link_with_profile_or_planum(image_document, planum_or_profile_document):
    __add_relation_target(planum_or_profile_document['resource'], 'isDepictedIn', image_document['resource']['id'])
    __add_relation_target(image_document['resource'], 'depicts', planum_or_profile_document['resource']['id'])

def __set_as_map_layer(image_document, project_document):
    __add_relation_target(project_document['resource'], 'hasMapLayer', image_document['resource']['id'])
    __add_relation_target(image_document['resource'], 'isMapLayerOf', 'project')

def __add_relation_target(resource, relation_name, relation_target_id):
    if 'relations' not in resource:
        resource['relations'] = {}
    if relation_name not in resource['relations']:
        resource['relations'][relation_name] = []
    if relation_target_id not in resource['relations'][relation_name]:
        resource['relations'][relation_name].append(relation_target_id)

def __get_image_bytes(pil_image_object, format, quality=None):
    out_bytes = io.BytesIO()
    if quality is not None:
        pil_image_object.save(out_bytes, format, quality=quality)
    else:
        pil_image_object.save(out_bytes, format)
    return out_bytes

def __generate_thumbnail(pil_image_object):
    converted_image = pil_image_object.convert('RGB')
    converted_image.thumbnail((10 * settings.ImageImporter.THUMBNAIL_HEIGHT, settings.ImageImporter.THUMBNAIL_HEIGHT))
    return __get_image_bytes(converted_image, 'jpeg', quality=settings.ImageImporter.THUMBNAIL_JPEG_QUALITY)

def __get_georeference(image_data, width, height):
    try:
        geotiff = GeoTiff(io.BytesIO(image_data.getvalue()))
        original_crs = geotiff.crs_code
        geotiff = GeoTiff(io.BytesIO(image_data.getvalue()), as_crs=original_crs)

        upper_left = geotiff.get_coords(0, height)
        upper_right = geotiff.get_coords(width, height)
        lower_left = geotiff.get_coords(0, 0)
    
        return {
            'topLeftCoordinates': [upper_left[1], upper_left[0]],
            'topRightCoordinates': [upper_right[1], upper_right[0]],
            'bottomLeftCoordinates': [lower_left[1], lower_left[0]]
        }
    except Exception:
        return None
