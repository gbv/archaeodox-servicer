from dpath import util as dp
from uuid import uuid4
from pathlib import Path

from app import settings, messages
from app.geo.postgres_database import PostgresDatabase
from app.geo.geoserver import Geoserver
from app.field.hub import FieldHub
from app.field.database import FieldDatabase


def run(field_documents, project_identifier, logger):
    postgres_database = PostgresDatabase()
    field_database = __get_field_database(project_identifier)
    try:
        postgres_database.open_connection()
        for field_document in __get_sorted_documents(field_documents):
            __process_record(field_document, project_identifier, postgres_database, Geoserver(), field_database, logger)
    finally:
        postgres_database.close_connection()

def __get_field_database(project_identifier):
    field_hub = FieldHub(
        settings.Couch.HOST_URL,
        settings.FieldHub.TEMPLATE_PROJECT_NAME,
        auth_from_module=True
    )
    return FieldDatabase(
        field_hub,
        project_identifier,
        settings.Couch.ADMIN_USER,
        settings.Couch.ADMIN_PASSWORD
    )

def __get_sorted_documents(field_documents):
    result = field_documents.copy()
    result.sort(key=lambda field_document: settings.Postgres.UPDATE_ORDER.index(field_document['resource']['category']))
    return result

def __process_record(field_document, project_identifier, database, geoserver, field_database, logger):
    __update_record(field_document, project_identifier, database)
    if field_document['resource']['category'] == 'Project':
        __update_processors(field_document, database)
    elif field_document['resource']['category'] == 'PlanDrawing':
        __update_wms_layer(field_document, geoserver, field_database, logger)

def __update_record(field_document, project_identifier, database):
    sql = __get_sql(field_document, project_identifier, database)
    if sql is not None:
        database.execute_write_query(sql)

def __get_sql(field_document, project_identifier, database):
    table_settings = __get_table_settings(field_document)
    if (table_settings is None):
        return None

    values = __get_values(field_document, project_identifier, database, table_settings['columns'])
    return (
        'INSERT INTO ' + table_settings['table_name'] + ' (' + ', '.join(values.keys()) + ', version) '
        'VALUES (' + ', '.join(values.values()) + ', 0) '
        'ON CONFLICT (pkey) DO UPDATE SET ' + __get_update_statement(table_settings['table_name'], values) + ';'
    )

def __get_update_statement(table_name, values):
    parts = []
    for key, value in values.items():
        parts.append(f'{key} = {value}')
    return ', '.join(parts) + ', version = ' + table_name + '.version + 1'

def __get_table_settings(field_document):
    category = field_document['resource']['category']
    return settings.Postgres.CATEGORIES.get(category, None)

def __get_values(field_document, project_identifier, database, column_names):
    values = {
        'pkey': __get_pkey(field_document, database),
        'identifier': __get_string_value(field_document, 'resource/identifier'),
        'short_name': __get_text_field_value(field_document, 'resource/shortName'),
        'short_description': __get_text_field_value(field_document, 'resource/shortDescription'),
        'short_description_addendum': __get_text_field_value(field_document, 'resource/shortDescriptionAddendum'),
        'documentation_unit': __get_string_array_value(field_document, 'resource/archaeoDox:documentationUnit'),
        'web_gis_id': __get_number_value(field_document, 'resource/webGisId'),
        'epsg_id': __get_number_value(field_document, 'resource/epsgId'),
        'geom': __get_geometry(field_document),
        'height': __get_height(field_document),
        'mtime': 'current_timestamp'
    }
    __add_relations(values, field_document, database)
    __add_project(values, field_document, project_identifier, database)

    return { column_name: value for column_name, value in values.items() if value is not None and column_name in column_names }

def __add_relations(values, field_document, database):
    values['relations_is_recorded_in'] = __get_relation_value(field_document, 'resource/relations/isRecordedIn')
    values['relations_is_present_in'] = __get_relation_value(field_document, 'resource/relations/isPresentIn')
    values['relations_depicts'] = __get_relation_value(field_document, 'resource/relations/depicts')
    values['relations_is_map_layer_of'] = __get_relation_value(field_document, 'resource/relations/isMapLayerOf')

    if field_document['resource']['category'] == 'Sample':
        __add_lies_within_relation_values_for_sample(values, field_document, database)
    else:
        values['relations_lies_within'] = __get_relation_value(field_document, 'resource/relations/liesWithin')

def __add_project(values, field_document, project_identifier, database):
    if field_document['resource']['category'] != 'ExcavationArea':
        return
    values['project'] = __get_project_pkey(project_identifier, database)

def __add_lies_within_relation_values_for_sample(values, field_document, database):
    target_ids = dp.get(field_document, 'resource/relations/liesWithin', default=None)
    if target_ids is None or len(target_ids) == 0:
        return
    target_id = target_ids[0]
    __add_lies_within_relation_for_sample(values, target_id, 'feature', database)
    __add_lies_within_relation_for_sample(values, target_id, 'find', database)

def __add_lies_within_relation_for_sample(values, target_id, table_name, database):
    if __is_existing(target_id, table_name, database):
        values['relations_lies_within_' + table_name] = __add_quotes(target_id)
    else:
        values['relations_lies_within_' + table_name] = 'NULL'

def __get_pkey(field_document, database):
    if field_document['resource']['category'] == 'Project':
        return __get_or_create_project_pkey(field_document, database)
    else:
        return __get_string_value(field_document, 'resource/id')
    
def __get_or_create_project_pkey(project_document, database):
    identifier = dp.get(project_document, 'resource/identifier', default=None)
    if identifier is None:
        return 'NULL'
    pkey = __get_project_pkey(identifier, database)
    if pkey is not None:
        return pkey
    else:
        return __add_quotes(str(uuid4()))
    
def __get_project_pkey(project_identifier, database):
    results = database.execute_read_query('SELECT pkey FROM project WHERE identifier = \'' + project_identifier + '\'')
    if len(results) == 0:
        return None
    else:
        return __add_quotes(str(results[0][0]))

def __get_string_value(field_document, field_path):
    value = dp.get(field_document, field_path, default=None)
    if value is None:
        return 'NULL'
    else:
        return __add_quotes(value)

def __get_string_array_value(field_document, field_path):
    values = dp.get(field_document, field_path, default=None)
    if values is None or len(values) == 0:
        return 'NULL'
    else:
        return __add_quotes(','.join(values))

def __get_text_field_value(field_document, field_path):
    value = dp.get(field_document, field_path, default=None)
    if value is None:
        return 'NULL'
    elif isinstance(value, str):
        return __add_quotes(value)
    else:
        return __add_quotes(value.get('de', None))

def __get_number_value(field_document, field_path):
    value = dp.get(field_document, field_path, default=None)
    if value is None:
        return 'NULL'
    else:
        return str(value)
    
def __get_relation_value(field_document, field_path):
    targetIds = dp.get(field_document, field_path, default=None)
    if targetIds is None or len(targetIds) == 0:
        return 'NULL'
    else:
        return __add_quotes(targetIds[0])

def __add_quotes(value):
    if value is None:
        return 'NULL'
    else:
        return '\'' + value + '\''

def __get_geometry(field_document):
    geojson = __get_geojson(field_document)
    if geojson is None:
        return 'NULL'
    else:
        return 'ST_Force3D(ST_MakeValid(ST_SetSRID(ST_GeomFromGeoJSON(\'' + geojson + '\'), 25832)))'
    
def __get_geojson(field_document):
    geometry = dp.get(field_document, 'resource/geometry', default=None)
    if geometry is None:
        return None
    else:
        return str(geometry).replace('\'', '"')

def __get_height(field_document):
    geometry = dp.get(field_document, 'resource/geometry', default=None)
    if geometry is None or geometry['type'] != 'Point' or len(geometry['coordinates']) != 3:
        return 'NULL'
    else:
        return str(geometry['coordinates'][2])

def __is_existing(target_id, table_name, database):
    results = database.execute_read_query('SELECT * FROM ' + table_name + ' WHERE pkey = \'' + target_id + '\'')
    return len(results) == 1

def __update_processors(project_document, database):
    processors = dp.get(project_document, 'resource/staff', default=[])
    for processor in processors:
        name = __get_processor_name(processor)
        if name is not None and __get_processor_pkey(name, database) is None:
            __create_processor(name, database)

def __get_processor_name(processor):
    if isinstance(processor, str):
        return processor
    else:
        return processor.get('value', None)

def __get_processor_pkey(processor_name, database):
    results = database.execute_read_query('SELECT pkey FROM processor WHERE name = \'' + processor_name + '\'')
    if len(results) == 0:
        return None
    else:
        return str(results[0][0])

def __create_processor(processor_name, database):
    pkey = str(uuid4())
    database.execute_write_query(f'INSERT INTO processor (pkey, name) VALUES (\'{pkey}\', \'{processor_name}\')')

def __update_wms_layer(image_document, geoserver, field_database, logger):
    image_data = __fetch_image_data(image_document, field_database, logger)
    layer_name = __get_wms_layer_name(image_document)
    geoserver.create_or_update_wms_layer(layer_name, image_data)

def __get_wms_layer_name(image_document):
    identifier = image_document['resource']['identifier']
    return Path(identifier).stem.replace(' ', '_').replace('.', '_')

def __fetch_image_data(image_document, field_database, logger):
    try:
        return field_database.download_image(image_document['resource']['id'], 'original_image')
    except Exception:
        message = messages.GeoUpdater.ERROR_IMAGE_DOWNLOAD_FAILED
        raise ValueError(message.replace('$VALUE', image_document['resource']['identifier']))
