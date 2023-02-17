import io, json
from tempfile import mkdtemp
from glob import glob
from os.path import join, basename
from shutil import rmtree
from osgeo import gdal
from zipfile import ZipFile

from app import messages


def run(file_data, field_database):
    file_bytes = io.BytesIO(file_data)
    zip_file = ZipFile(file_bytes, 'r')
    geojson = __convert_to_geojson(zip_file)
    segment_count = 0
    for feature in geojson['features']:
        segment_count += 1
        __import_geometry(feature['geometry'], feature['properties'], field_database, segment_count)

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

def __import_geometry(geometry, properties, field_database, segment_count):
    planum_or_profile_identifier = properties.get('exca_int')
    planum_or_profile_short_description = __get_planum_or_profile_short_description(properties)
    planum_or_profile_category = __get_planum_or_profile_category(properties)
    feature_complex_identifier = properties.get('group')
    feature_complex_short_description = properties.get('group_info')
    feature_identifier = properties.get('strat_unit')
    feature_segment_identifier = __get_feature_segment_identifier(feature_identifier, segment_count)
    feature_segment_short_description = properties.get('info')

    __validate(planum_or_profile_identifier, planum_or_profile_category)

    trench = __update_trench(field_database)
    planum_or_profile = __update_planum_or_profile(
        field_database, trench, planum_or_profile_identifier, planum_or_profile_short_description,
        planum_or_profile_category, geometry=geometry if feature_identifier is None else None
    )
    
    if feature_identifier is not None:
        feature_complex = __update_feature_complex(
            field_database, trench, planum_or_profile, feature_complex_identifier, feature_complex_short_description
        )
        feature = __update_feature(field_database, trench, planum_or_profile, feature_complex, feature_identifier)
        __update_feature_segment(
            field_database, trench, planum_or_profile, feature, feature_segment_identifier,
            feature_segment_short_description, geometry
        )
    
def __get_planum_or_profile_short_description(properties):
    part1 = __read_value('part1_info', properties) + ' ' + __read_value('part1', properties)
    part2 = __read_value('part2_info', properties) + ' ' + __read_value('part2', properties)
    result = part1 + ', ' + part2
    return result.strip()

def __read_value(attribute_name, properties):
    value = properties.get(attribute_name)
    if value is None:
        return ''
    else:
        return value

def __get_planum_or_profile_category(properties):
    if 'FLZ' in properties['file_name']:
        return 'Planum'
    elif 'PRZ' in properties['file_name']:
        return 'Profile'
    else:
        return None

def __get_feature_segment_identifier(feature_identifier, count):
    if feature_identifier is None:
        return None
    
    return f'BA{feature_identifier}-{count}'

def __validate(planum_or_profile_identifier, planum_or_profile_category):
    if planum_or_profile_category is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_INVALID_NAME)
    elif planum_or_profile_identifier is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_MISSING_EXCA_INT)

def __update_trench(field_database):
    return field_database.get_or_create_document('Untersuchungsfläche', 'Trench')

def __update_planum_or_profile(field_database, trench, identifier, short_description, category, geometry=None):
    resource_data = {
        'identifier': str(identifier),
        'category': category,
        'shortDescription': short_description,
        'relations': {
            'isRecordedIn': [trench['resource']['id']]
        }
    }

    if geometry is not None:
        resource_data['geometry'] = geometry

    return field_database.populate_resource(resource_data)

def __update_feature_complex(field_database, trench, planum_or_profile, identifier, short_description):    
    if identifier is None:
        return None

    resource_data = {
        'identifier': str(identifier),
        'category': 'FeatureGroup',
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']]
        }
    }

    if short_description is not None:
        resource_data['amh-default:shortDescriptionFreetext'] = short_description
    
    return field_database.populate_resource(resource_data)

def __update_feature(field_database, trench, planum_or_profile, feature_complex, identifier):
    if identifier is None:
        return None

    resource_data = {
        'identifier': str(identifier),
        'category': 'Feature',
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    if feature_complex is not None:
        resource_data['relations']['liesWithin'] = [feature_complex['resource']['id']]

    return field_database.populate_resource(resource_data)

def __update_feature_segment(field_database, trench, planum_or_profile, feature, identifier, short_description,
                             geometry):
    if identifier is None:
        return None

    resource_data = {
        'identifier': str(identifier),
        'category': 'FeatureSegment',
        'geometry': geometry,
        'relations': {
            'isRecordedIn': [trench['resource']['id']],
            'liesWithin': [feature['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    if short_description is not None:
        resource_data['amh-default:shortDescriptionFreetext'] = short_description

    return field_database.populate_resource(resource_data)
