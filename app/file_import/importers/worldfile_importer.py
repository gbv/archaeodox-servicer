from app import settings, messages


def run(worldfile_data, worldfile_name, field_database):
    image_file_extensions = __get_image_file_extensions()
    image_document = __get_image_document(worldfile_name, field_database, image_file_extensions)
    changed_fields = {
         'georeference': __create_georeference(
            worldfile_data,
            int(image_document['resource']['width']),
            int(image_document['resource']['height'])
        )
    }
    field_database.populate_resource(changed_fields, image_document['resource']['identifier'])

def __get_image_file_extensions():
    formats = []
    for document_type_configuration in settings.FileImport.IMPORT_MAPPING.values():
        for format in document_type_configuration['importers'].get('image', []):
            if format not in formats:
                formats.append(format)
    format_settings = settings.FileImport.FORMATS
    return filter(lambda extension: format_settings[extension]['file_type'] in formats, format_settings.keys())

def __get_image_document(worldfile_name, field_database, image_file_extensions):
        possible_image_file_names = __get_possible_image_file_names(worldfile_name, image_file_extensions)
        documents = field_database.search({
            'selector': {
                'resource.identifier': {
                    '$in': possible_image_file_names
                }
            }
        });
        if len(documents) == 1:
             return documents[0]
        else:
             raise ValueError(messages.FileImport.ERROR_NO_WORLDFILE_MATCH)

def __get_possible_image_file_names(worldfile_name, image_file_extensions):
    possible_image_file_names = []
    for extension in image_file_extensions:
        possible_image_file_names.append(__get_image_name(worldfile_name, extension.lower()))
        possible_image_file_names.append(__get_image_name(worldfile_name, extension.upper()))
    return possible_image_file_names

def __get_image_name(worldfile_name, image_file_extension):
    extension = worldfile_name.split('.')[-1]
    base_name = worldfile_name.replace('.' + extension, '')
    return base_name + '.' + image_file_extension

def __create_georeference(worldfile_data, width, height):
    values = __get_worldfile_values(worldfile_data.decode('utf-8'))

    topLeftCoordinates = computeLatLng(0, 0, values);
    topRightCoordinates = computeLatLng(width - 1, 0, values);
    bottomLeftCoordinates = computeLatLng(0, height - 1, values);

    return {
        'topLeftCoordinates': topLeftCoordinates,
        'topRightCoordinates': topRightCoordinates,
        'bottomLeftCoordinates': bottomLeftCoordinates
    }

def __get_worldfile_values(worldfile_data):
     lines = worldfile_data.split('\n')
     cleaned_lines = list(filter(lambda line: len(line) > 0, lines))

     if len(cleaned_lines) == 6:
        return __parse_as_float(cleaned_lines)
     else:
        raise ValueError(messages.FileImport.ERROR_INVALID_WORLDFILE)

def __parse_as_float(worldfile_lines):
    result = []
    for line in worldfile_lines:
        try:
            result.append(float(line))
        except:
            raise ValueError(messages.FileImport.ERROR_INVALID_WORLDFILE)
    return result

def computeLatLng(imageX, imageY, worldfileValues):
    latPosition = worldfileValues[3] * imageY
    latRotation = worldfileValues[1] * imageX
    latTranslation = worldfileValues[5]
    lat = latPosition + latRotation + latTranslation

    lngPosition = worldfileValues[0] * imageX
    lngRotation = worldfileValues[2] * imageY
    lngTranslation = worldfileValues[4]
    lng = lngPosition + lngRotation + lngTranslation

    return [lat, lng]
