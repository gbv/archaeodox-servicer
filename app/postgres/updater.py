from dpath import util as dp

from app import settings
from app.postgres.database import PostgresDatabase


def run(field_documents):
    database = PostgresDatabase()
    try:
        database.open_connection()
        for field_document in field_documents:
            __update_record(field_document, database)
    finally:
        database.close_connection()

def __update_record(field_document, database):
    sql = __get_sql(field_document)
    if sql is not None:
        database.execute_query(sql)

def __get_sql(field_document):
    table_name = __get_table_name(field_document)
    if (table_name is None):
        return None

    values = __get_values(field_document)
    return (
        'INSERT INTO ' + table_name + ' (' + ', '.join(values.keys()) + ', version) '
        'VALUES (' + ', '.join(values.values()) + ', 0) '
        'ON CONFLICT (pkey) DO UPDATE SET ' + __get_update_statement(table_name, values) + ';'
    )

def __get_update_statement(table_name, values):
    parts = []
    for key, value in values.items():
        parts.append(f'{key} = {value}')
    return ', '.join(parts) + ', version = ' + table_name + '.version + 1'

def __get_table_name(field_document):
    category = field_document['resource']['category']
    return settings.Postgres.TABLE_NAMES.get(category, None)

def __get_values(field_document):
    values = {
        'pkey': __get_string_value(field_document, 'resource/id'),
        'identifier': __get_string_value(field_document, 'resource/identifier'),
        'short_description': __get_text_field_value(field_document, 'resource/shortDescription'),
        'short_description_addendum': __get_text_field_value(field_document, 'resource/shortDescriptionAddendum'),
        'relations_is_recorded_in': __get_relation_value(field_document, 'resource/relations/isRecordedIn'),
        'relations_lies_within': __get_relation_value(field_document, 'resource/relations/liesWithin'),
        'relations_is_present_in': __get_relation_value(field_document, 'resource/relations/isPresentIn'),
        'geom': __get_geometry(field_document),
        'mtime': 'current_timestamp'
    }
    return { key: value for key, value in values.items() if value is not None }

def __get_string_value(field_document, field_path):
    value = dp.get(field_document, field_path, default=None)
    return __add_quotes(value)
    
def __get_text_field_value(field_document, field_path):
    value = dp.get(field_document, field_path, default=None)
    if value is None:
        return None
    elif isinstance(value, str):
        return __add_quotes(value)
    else:
        return __add_quotes(value.get('de', None))
    
def __get_relation_value(field_document, field_path):
    targetIds = dp.get(field_document, field_path, default=None)
    if targetIds is None or len(targetIds) == 0:
        return None
    else:
        return __add_quotes(targetIds[0])

def __add_quotes(value):
    if value is None:
        return None
    else:
        return '\'' + value + '\''

def __get_geometry(field_document):
    geojson = __get_geojson(field_document)
    if geojson is None:
        return None
    else:
        return 'ST_GeomFromGeoJSON(\'' + geojson + '\')'

def __get_geojson(field_document):
    geometry = dp.get(field_document, 'resource/geometry', default=None)
    if geometry is None:
        return None
    else:
        return str(geometry).replace('\'', '"')
