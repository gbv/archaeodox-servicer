from dpath import util as dp
from uuid import uuid4

from app import settings
from app.postgres.database import PostgresDatabase


def run(field_documents):
    database = PostgresDatabase()
    try:
        database.open_connection()
        for field_document in __get_sorted_documents(field_documents):
            __process_record(field_document, database)
    finally:
        database.close_connection()

def __get_sorted_documents(field_documents):
    result = field_documents.copy()
    result.sort(key=lambda field_document: settings.Postgres.UPDATE_ORDER.index(field_document['resource']['category']))
    return result

def __process_record(field_document, database):
    __update_record(field_document, database)
    if field_document['resource']['category'] == 'Project':
        __update_processors(field_document, database)

def __update_record(field_document, database):
    sql = __get_sql(field_document, database)
    if sql is not None:
        database.execute_write_query(sql)

def __get_sql(field_document, database):
    table_settings = __get_table_settings(field_document)
    if (table_settings is None):
        return None

    values = __get_values(field_document, database, table_settings['columns'])
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

def __get_values(field_document, database, column_names):
    values = {
        'pkey': __get_string_value(field_document, 'resource/id'),
        'identifier': __get_string_value(field_document, 'resource/identifier'),
        'short_name': __get_text_field_value(field_document, 'resource/shortName'),
        'short_description': __get_text_field_value(field_document, 'resource/shortDescription'),
        'short_description_addendum': __get_text_field_value(field_document, 'resource/shortDescriptionAddendum'),
        'documentation_unit': __get_string_array_value(field_document, 'resource/archaeoDox:documentationUnit'),
        'web_gis_id': __get_number_value(field_document, 'resource/webGisId'),
        'epsg_id': __get_number_value(field_document, 'resource/epsgId'),
        'geom': __get_geometry(field_document),
        'mtime': 'current_timestamp'
    }
    __add_relations(values, field_document, database)

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
        return 'ST_GeomFromGeoJSON(\'' + geojson + '\')'

def __get_geojson(field_document):
    geometry = dp.get(field_document, 'resource/geometry', default=None)
    if geometry is None:
        return None
    else:
        return str(geometry).replace('\'', '"')
    
def __is_existing(target_id, table_name, database):
    results = database.execute_read_query('SELECT * FROM ' + table_name + ' WHERE pkey = \'' + target_id + '\'')
    return len(results) == 1

def __update_processors(project_document, database):
    processors = dp.get(project_document, 'resource/staff', default=[])
    for processor in processors:
        name = __get_processor_name(processor)
        if name is not None and not __is_processor_existing(name, database):
            __create_processor(name, database)

def __get_processor_name(processor):
    if isinstance(processor, str):
        return processor
    else:
        return processor.get('value', None)

def __is_processor_existing(processor_name, database):
    results = database.execute_read_query('SELECT * FROM processor WHERE name = \'' + processor_name + '\'')
    if len(results) == 0:
        return False
    else:
        return True

def __create_processor(processor_name, database):
    pkey = str(uuid4())
    database.execute_write_query(f'INSERT INTO processor (pkey, name) VALUES (\'{pkey}\', \'{processor_name}\')')
