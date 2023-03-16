import io, json
from tempfile import mkdtemp
from glob import glob
from os.path import join, basename
from shutil import rmtree
from osgeo import gdal
from zipfile import ZipFile

from app import settings, messages


def run(file_data, field_database):
    file_bytes = io.BytesIO(file_data)
    zip_file = ZipFile(file_bytes, 'r')
    geojson = __convert_to_geojson(zip_file)
    for feature in geojson['features']:
        __import_geometry(feature['geometry'], feature['properties'], field_database)

def __convert_to_geojson(zip_file):
    try:
        temp_directory = mkdtemp()
        zip_file.extractall(temp_directory)
        shape_files = glob(join(temp_directory, '**', '*.shp'), recursive=True)
        features = []
        geojson_path = join(temp_directory, 'result.geojson')
        options = gdal.VectorTranslateOptions(format='GeoJSON')

        for shape_file in shape_files:
            shape_file_name = basename(shape_file)
            gdal.VectorTranslate(geojson_path, shape_file, options=options)
        
            with open(geojson_path, 'r') as geojson_data:
                collection = json.load(geojson_data)
                for feature in collection['features']:
                    feature['properties']['file_name'] = shape_file_name
            features += collection['features']
            
        return {
            'type': 'FeatureCollection',
            'features': features
        }
    finally:
        rmtree(temp_directory)

def __import_geometry(geometry, properties, field_database):
    import_type = __get_import_type(properties)
    if import_type is None:
        return

    planum_or_profile_category = __get_planum_or_profile_category(properties)
    planum_or_profile_identifier = __get_identifier(properties.get('exca_int'), planum_or_profile_category)
    planum_or_profile_short_description = __get_planum_or_profile_short_description(properties)
    feature_group_identifier = __get_identifier(properties.get('group'), 'FeatureGroup')
    feature_group_short_description = properties.get('group_info')
    feature_identifier = __get_identifier(properties.get('strat_unit'), 'Feature')
    feature_segment_short_description = properties.get('info')
    find_identifier = __get_identifier(properties.get('find'), 'Find')

    __validate(planum_or_profile_identifier, planum_or_profile_category)

    trench = __update_trench(field_database)
    planum_or_profile = __update_planum_or_profile(
        field_database, trench, planum_or_profile_identifier, planum_or_profile_short_description,
        planum_or_profile_category, geometry=geometry if feature_identifier is None else None
    )
    
    if import_type == 'featureSegment' and feature_identifier is not None:
        feature_group = __update_feature_group(
            field_database, trench, planum_or_profile, feature_group_identifier, feature_group_short_description
        )
        feature = __update_feature(field_database, trench, planum_or_profile, feature_group, feature_identifier)
        __update_feature_segment(
            field_database, trench, planum_or_profile, feature, feature_segment_short_description, geometry
        )
    elif import_type == 'find' and find_identifier is not None:
        feature = __update_feature(field_database, trench, planum_or_profile, None, feature_identifier)
        __update_find(field_database, trench, feature, find_identifier, geometry)

def __get_import_type(properties):
    for import_type, file_name_keywords in settings.ShapefileImporter.FILE_NAME_MAPPING.items():
        for keyword in file_name_keywords:
            if keyword in properties['file_name']:
                return import_type
    return None

def __get_planum_or_profile_short_description(properties):
    part1 = __read_value('part1_info', properties) + ' ' + __read_value('part1', properties)
    part2 = __read_value('part2_info', properties) + ' ' + __read_value('part2', properties)
    result = part1.strip() + ', ' + part2.strip()
    return result

def __read_value(attribute_name, properties):
    value = properties.get(attribute_name)
    if value is None:
        return ''
    else:
        return str(value)

def __get_planum_or_profile_category(properties):
    if settings.FileImport.CATEGORY_PREFIXES['Planum'] in properties['file_name']:
        return 'Planum'
    elif settings.FileImport.CATEGORY_PREFIXES['Profile'] in properties['file_name']:
        return 'Profile'
    else:
        return None

def __get_identifier(base_identifier, category):
    if base_identifier is None:
        return None

    return settings.FileImport.CATEGORY_PREFIXES[category] + str(base_identifier)

def __validate(planum_or_profile_identifier, planum_or_profile_category):
    if planum_or_profile_category is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_INVALID_NAME)
    elif planum_or_profile_identifier is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_MISSING_EXCA_INT)

def __update_trench(field_database):
    return field_database.get_or_create_document('Untersuchungsfläche', 'Trench')

def __update_planum_or_profile(field_database, trench, identifier, short_description, category, geometry=None):
    resource_data = {
        'identifier': identifier,
        'category': category,
        'shortDescription': { 'de': short_description },
        'relations': {
            'isRecordedIn': [trench['resource']['id']]
        }
    }

    if geometry is not None:
        resource_data['geometry'] = geometry

    return field_database.populate_resource(resource_data)

def __update_feature_group(field_database, trench, planum_or_profile, identifier, short_description):    
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': 'FeatureGroup',
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']]
        }
    }

    if short_description is not None:
        resource_data['amh-default:shortDescriptionFreetext'] = { 'de': short_description }
    
    return field_database.populate_resource(resource_data)

def __update_feature(field_database, trench, planum_or_profile, feature_group, identifier):
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': 'Feature',
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    if feature_group is not None:
        resource_data['relations']['liesWithin'] = [feature_group['resource']['id']]

    return field_database.populate_resource(resource_data)

def __update_feature_segment(field_database, trench, planum_or_profile, feature, short_description, geometry):
    resource_data = {
        'identifier': __get_feature_segment_identifier(feature, field_database),
        'category': 'FeatureSegment',
        'geometry': geometry,
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'liesWithin': [feature['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    if short_description is not None:
        resource_data['amh-default:shortDescriptionFreetext'] = { 'de': short_description }

    return field_database.populate_resource(resource_data)

def __update_find(field_database, trench, feature, identifier, geometry):
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': 'Find',
        'geometry': geometry,
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'liesWithin': [feature['resource']['id']]
        }
    }

    return field_database.populate_resource(resource_data)

def __get_feature_segment_identifier(feature, field_database):
    base_feature_identifier = __get_base_identifier(feature)
    number = __get_feature_segment_identifier_number(feature['resource']['id'], field_database)

    return __get_identifier(f'{base_feature_identifier}-{str(number)}', 'FeatureSegment')

def __get_feature_segment_identifier_number(feature_id, field_database):
    
    feature_segments = __get_existing_feature_segments(feature_id, field_database)
    numbers = sorted(map(__get_number_from_feature_segment, feature_segments))
    if len(numbers) == 0:
        return 1
    else:
        return numbers[-1] + 1

def __get_existing_feature_segments(feature_id, field_database):
    query = {
        'selector': {
            'resource.relations.liesWithin': {
                '$elemMatch': {
                    "$eq": feature_id
                }
            }
        } 
    }
    return field_database.search(query)

def __get_number_from_feature_segment(document):
    segments = document['resource']['identifier'].split('-')
    if len(segments) < 2:
        return 0
    else:
        return int(segments[1])

def __get_base_identifier(document):
    category = document['resource']['category']
    return document['resource']['identifier'].replace(settings.FileImport.CATEGORY_PREFIXES[category], '')
