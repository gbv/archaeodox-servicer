import mimetypes, io
from os.path import basename
from PIL import Image
from geotiff import GeoTiff

from app import settings


def run(image_data, image_name, field_database):
    image_document = field_database.get_or_create_document(image_name)
    id = image_document['_id']
    
    image_object = io.BytesIO(image_data)
    image = Image.open(io.BytesIO(image_object.getvalue()))
    __initialize_image_document(image_document, image_name, image)

    mimetype, encoding = mimetypes.guess_type(image_name)
    if mimetype is None:
        return
    if mimetype == 'image/tiff':
        __append_georeference(image_document, image_object)
    format = basename(mimetype)
    
    response = field_database.upload_image(id, __get_image_bytes(image, format), mimetype, 'original_image')
    if response.ok:
        field_database.upload_image(id, __generate_thumbnail(image, format), mimetype, 'thumbnail_image')
    else:
        raise ConnectionError(response.content)
    field_database.update_doc(id, image_document)

def __initialize_image_document(image_document, image_file_name, image):
    width, height = image.size
    resource = image_document['resource']
    if 'category' not in resource:
        # TODO Set correct category or remove if CSV import is mandatory
        resource['category'] = 'Image' 
    resource['width'] = width
    resource['height'] = height
    resource['originalFilename'] = image_file_name
    if 'relations' not in resource:
        resource['relations'] = {}

def __get_image_bytes(pil_image_object, format):
    out_bytes = io.BytesIO()
    pil_image_object.save(out_bytes, format)
    return out_bytes

def __generate_thumbnail(pil_image_object, format):
    cloned_image = pil_image_object.copy()
    cloned_image.thumbnail((10 * settings.FieldHub.THUMBNAIL_HEIGHT, settings.FieldHub.THUMBNAIL_HEIGHT))
    # TODO Convert to JPEG
    return __get_image_bytes(cloned_image, format)

def __append_georeference(image_document, image_data):
    width = image_document['resource']['width']
    height = image_document['resource']['height']

    try:
        geotiff = GeoTiff(io.BytesIO(image_data.getvalue()))
        original_crs = geotiff.crs_code
        geotiff = GeoTiff(io.BytesIO(image_data.getvalue()), as_crs=original_crs)

        upper_left = geotiff.get_coords(0, height)
        upper_right = geotiff.get_coords(width, height)
        lower_left = geotiff.get_coords(0, 0)
    
        image_document['resource']['georeference'] = {
            'topLeftCoordinates': [upper_left[1], upper_left[0]],
            'topRightCoordinates': [upper_right[1], upper_right[0]],
            'bottomLeftCoordinates': [lower_left[1], lower_left[0]]
        }
    except Exception:
        # TODO Error handling
        pass