import io, json
from tempfile import mkdtemp
from glob import glob
from os.path import join, basename
from shutil import rmtree
from osgeo import gdal
from zipfile import ZipFile
from jsondiff import diff

from app import settings, messages
from app.dante.database import DanteDatabase


def run(file_data, field_database):
    file_bytes = io.BytesIO(file_data)
    zip_file = ZipFile(file_bytes, 'r')
    geojson = __convert_to_geojson(zip_file)
    dante_database = DanteDatabase(settings.Dante.HOST_URL)
    for feature in geojson['features']:
        __import_geometry(feature['geometry'], feature['properties'], field_database, dante_database)

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

def __import_geometry(geometry, properties, field_database, dante_database):
    import_type = __get_import_type(properties)
    if import_type is None:
        return

    planum_or_profile_category = __get_planum_or_profile_category(properties)
    if import_type == 'referenceLines' and planum_or_profile_category != 'Profile':
        return
    
    sample_identifier = __get_sample_identifier(properties)
    if import_type == 'referencePoints' and sample_identifier is None:
        return

    planum_or_profile_identifier = __get_identifier(properties.get('exca_int'), planum_or_profile_category)
    planum_or_profile_short_description = __get_planum_or_profile_short_description(properties)
    feature_group_identifier = __get_identifier(properties.get('group'), 'FeatureGroup')
    feature_group_short_description_addendum = properties.get('group_info')
    feature_identifier = __get_identifier(properties.get('strat_unit'), 'Feature')
    feature_short_description = __get_feature_short_description(
        properties, 'amh_befunde', dante_database, properties['file_name']
    )
    feature_short_description_addendum = properties.get('info_alias')
    find_identifier = __get_identifier(properties.get('find'), 'Find')

    __validate(
        planum_or_profile_identifier, planum_or_profile_category, feature_identifier,
        import_type, properties['file_name']
    )

    excavation_area = __update_excavation_area(
        field_database, geometry if import_type == 'excavationArea' else None
    )

    if planum_or_profile_identifier is not None:
        planum_or_profile = __update_planum_or_profile(
            field_database, excavation_area, planum_or_profile_identifier, planum_or_profile_short_description,
            planum_or_profile_category, geometry if import_type == 'planumOrProfile' else None
        )
    
    if import_type == 'featureSegment' and feature_identifier is not None:
        feature_group = __update_feature_group(
            field_database, excavation_area, planum_or_profile, feature_group_identifier,
            feature_group_short_description_addendum
        )
        feature = __update_feature(
            field_database, excavation_area, planum_or_profile, feature_group, feature_identifier,
            feature_short_description, feature_short_description_addendum
        )
        __update_feature_segment(
            field_database, excavation_area, planum_or_profile, feature, geometry
        )
    elif import_type == 'find' and find_identifier is not None:
        feature = __update_feature(
            field_database, excavation_area, planum_or_profile, None, feature_identifier, feature_short_description,
            feature_short_description_addendum
        )
        __update_find_or_sample(field_database, excavation_area, feature, find_identifier, geometry, 'Find')
    elif import_type == 'referencePoints' and sample_identifier is not None:
        feature = __update_feature(
            field_database, excavation_area, planum_or_profile, None, feature_identifier, feature_short_description,
            feature_short_description_addendum
        )
        __update_find_or_sample(field_database, excavation_area, feature, sample_identifier, geometry, 'Sample')

def __get_import_type(properties):
    for import_type, file_name_keywords in settings.ShapefileImporter.FILE_NAME_MAPPING.items():
        for keyword in file_name_keywords:
            if keyword in properties['file_name']:
                return import_type
    if __is_excavation_area(properties):
        return 'excavationArea'
    else:
        return None

def __get_planum_or_profile_short_description(properties):
    part1 = __read_value('part1_info', properties) + ' ' + __read_value('part1', properties)
    part2 = __read_value('part2_info', properties) + ' ' + __read_value('part2', properties)
    result = part1.strip() + ', ' + part2.strip()
    return result

def __get_feature_short_description(properties, vocabulary_name, dante_database, file_name):
    concept_label = properties.get('info')
    return __get_concept_id(concept_label, vocabulary_name, dante_database, file_name)

def __get_concept_id(concept_label, vocabulary_name, dante_database, file_name):
    concept_label = concept_label.strip()
    results = dante_database.search(vocabulary_name, concept_label)
    for result in results:
        if result['prefLabel']['de'].strip() == concept_label:
            return result['uri'].split('/')[-1]
    raise ValueError(f'{messages.FileImport.ERROR_SHAPEFILE_CONCEPT_NOT_FOUND} {concept_label} ({file_name})')

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

def __get_sample_identifier(properties):
    if __is_sample(properties):
        return __get_identifier(properties.get('refpoint'), 'Sample')
    else:
        return None

def __is_excavation_area(properties):
    return settings.ShapefileImporter.EXCAVATION_AREA_KEYWORD.lower() in properties.get('info', '').lower()

def __is_sample(properties):
    return settings.ShapefileImporter.SAMPLE_KEYWORD.lower() in properties.get('info', '').lower()

def __validate(planum_or_profile_identifier, planum_or_profile_category, feature_identifier,
               import_type, file_name):
    if import_type == 'excavationArea':
        return
    elif planum_or_profile_category is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_INVALID_NAME + ' ' + file_name)
    elif planum_or_profile_identifier is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_MISSING_EXCA_INT + ' ' + file_name)
    elif import_type in ['featureSegment', 'referencePoints'] and feature_identifier is None:
        raise ValueError(messages.FileImport.ERROR_SHAPEFILE_MISSING_STRAT_UNIT + ' ' + file_name)

def __update_excavation_area(field_database, geometry):
    resource_data = {
        'identifier': 'Untersuchungsfläche',
        'category': 'ExcavationArea',
        'relations': {}
    }

    if geometry is not None:
        resource_data['geometry'] = geometry

    return field_database.populate_resource(resource_data)

def __update_planum_or_profile(field_database, excavation_area, identifier, short_description, category, geometry):
    resource_data = {
        'identifier': identifier,
        'category': category,
        'shortDescription': { 'de': short_description },
        'relations': {
            'isRecordedIn': [excavation_area['resource']['id']]
        }
    }

    if geometry is not None:
        resource_data['geometry'] = geometry

    return field_database.populate_resource(resource_data)

def __update_feature_group(field_database, excavation_area, planum_or_profile, identifier,
                           short_description_addendum):    
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': 'FeatureGroup',
        'relations': {
            'isRecordedIn': [excavation_area['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']]
        }
    }

    if short_description_addendum is not None:
        resource_data['shortDescriptionAddendum'] = { 'de': short_description_addendum }
    
    return field_database.populate_resource(resource_data)

def __update_feature(field_database, excavation_area, planum_or_profile, feature_group, identifier,
                     short_description, short_description_addendum):
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': 'Feature',
        'relations': {
            'isRecordedIn': [excavation_area['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    if short_description is not None:
        resource_data['shortDescription'] = short_description
    if short_description_addendum is not None:
        resource_data['shortDescriptionAddendum'] = { 'de': short_description_addendum }
    if feature_group is not None:
        resource_data['relations']['liesWithin'] = [feature_group['resource']['id']]

    return field_database.populate_resource(resource_data)

def __update_feature_segment(field_database, excavation_area, planum_or_profile, feature, geometry):
    existing_feature_segments = __get_existing_feature_segments(feature['resource']['id'], field_database)
    if __is_existing(geometry, existing_feature_segments):
        return None

    resource_data = {
        'identifier': __get_feature_segment_identifier(feature, existing_feature_segments),
        'category': 'FeatureSegment',
        'geometry': geometry,
        'relations': {
            'isRecordedIn': [excavation_area['resource']['id']],
            'liesWithin': [feature['resource']['id']],
            'isPresentIn': [planum_or_profile['resource']['id']],
        }
    }

    return field_database.populate_resource(resource_data)

def __update_find_or_sample(field_database, excavation_area, feature, identifier, geometry, category):
    if identifier is None:
        return None

    resource_data = {
        'identifier': identifier,
        'category': category,
        'geometry': geometry,
        'relations': {
            'isRecordedIn': [excavation_area['resource']['id']]
        }
    }

    if feature is not None:
        resource_data['relations']['liesWithin'] = [feature['resource']['id']]

    return field_database.populate_resource(resource_data)

def __get_feature_segment_identifier(feature, existing_feature_segments):
    base_feature_identifier = __get_base_identifier(feature)
    number = __get_feature_segment_identifier_number(existing_feature_segments)

    return __get_identifier(f'{base_feature_identifier}-{str(number)}', 'FeatureSegment')

def __get_feature_segment_identifier_number(existing_feature_segments):
    numbers = sorted(map(__get_number_from_feature_segment, existing_feature_segments))
    if len(numbers) == 0:
        return 1
    else:
        return numbers[-1] + 1

def __get_existing_feature_segments(feature_id, field_database):
    query = {
        'selector': {
            'resource.relations.liesWithin': {
                '$elemMatch': {
                    '$eq': feature_id
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

def __is_existing(geometry, existing_feature_segments):
    for feature_segment in existing_feature_segments:
        feature_segment_geometry = feature_segment['resource']['geometry']
        if feature_segment_geometry is not None and diff(geometry, feature_segment_geometry) == {}:
            return True
    return False
