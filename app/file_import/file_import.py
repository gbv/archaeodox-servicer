import requests
from dpath import util as dp

from app import settings, messages
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.field import error_messages as field_error_messages
from app.file_import.importers import image_importer, csv_importer, shapefile_importer


def perform_import(import_object, easydb):
    easydb.acquire_session()
    files = __get_files(import_object, easydb)
    __import_files(files, import_object, easydb)

def __get_files(import_object, easydb):
    id = import_object['_id']
    wrapped_object_data = easydb.get_object_by_id('import', id)
    inner_object_data = wrapped_object_data['import']
    nested_files = '_nested:import__dateien'
    
    files = []
    for file in inner_object_data[nested_files]:
        file_information = file['datei'][0]
        file_name = file_information['original_filename']
        file_extension = file_name.split('.')[-1]
        files.append({
            'name': file_name,
            'url': dp.get(file_information, 'versions/original/download_url'),
            'format_settings': settings.FileImportingHandler.FORMATS.get(file_extension, None),
            'detected_format': file_information['extension']
        })
    return files

def __import_files(files, import_object, easydb):
    database = __create_field_database(import_object)
    results = []

    for file in files:
        result = __import_file(file, database, easydb)
        results.append(result)

    __create_result_object(results, import_object, easydb)

def __import_file(file, database, easydb):
    result = {
        'dokument': __get_cloned_asset(file, easydb),
        'dokumententyp': __get_file_type_object(file, easydb)
    }

    try:
        __validate(file, result['dokumententyp'], database)
        file_data = __get_file_data(file['url'])
        __run_importer(file, file_data, database)
        result['fehlermeldung'] = messages.FileImportingHandler.SUCCESS
    except Exception as error:
        result['fehlermeldung'] = __get_error_message(str(error))
    
    return result

def __get_cloned_asset(file, easydb):
    cloned_asset = easydb.create_asset_from_url(file['name'], file['url'])
    cloned_asset[0]['preferred'] = True
    return cloned_asset

def __get_file_type_object(file, easydb):
    if file['format_settings'] is None:
        return None
    else:
        return easydb.get_object_by_field_value('dateityp', 'name', file['format_settings']['file_type'])

def __validate(file, file_type_object, database):
    if database is None:
        raise ValueError(messages.FileImportingHandler.ERROR_MISSING_CREDENTIALS)
    if file_type_object is None:
        raise ValueError(messages.FileImportingHandler.ERROR_UNSUPPORTED_FILE_FORMAT)
    if file['format_settings']['expected_format'] != file['detected_format']:
        raise ValueError(messages.FileImportingHandler.ERROR_INVALID_FILE_FORMAT)

def __get_file_data(url):
    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        raise ValueError(response.text)

def __run_importer(file, file_data, database):
    if file['format_settings']['importer'] == 'image':
        image_importer.run(file_data, file['name'], database)
    if file['format_settings']['importer'] == 'csv':
        csv_importer.run(file_data, file['name'], database)
    if file['format_settings']['importer'] == 'shapefile':
        shapefile_importer.run(file_data, database)

def __create_field_database(import_object):
    if 'vorgangsname' not in import_object or 'passwort' not in import_object:
        return None
    field_hub = FieldHub(
        settings.Couch.HOST_URL,
        settings.FieldHub.TEMPLATE_PROJECT_NAME,
        auth_from_module=True
    )
    db_name = import_object['vorgangsname']
    password = import_object['passwort']
    return FieldDatabase(field_hub, db_name, password)

def __create_result_object(file_import_results, import_object, easydb):
    fields_data = {
        '_nested:import_ergebnis__dokument': file_import_results
    }
    tags = __get_tags(__is_failed(file_import_results))
    easydb.create_object('import_ergebnis', fields_data, pool=import_object['_pool'], tags=tags)

def __is_failed(file_import_results):
    for result in file_import_results:
        if result['fehlermeldung'] != messages.FileImportingHandler.SUCCESS:
            return True
    return False

def __get_tags(failed):
    if failed:
        return [{ '_id': settings.FileImportingHandler.FAILURE_TAG_ID }]
    else:
        return [{ '_id': settings.FileImportingHandler.SUCCESS_TAG_ID }]

def __get_error_message(error):
    if error == field_error_messages.FIELD_HUB_INVALID_CREDENTIALS:
        error = messages.FileImportingHandler.ERROR_INVALID_CREDENTIALS
    
    return messages.FileImportingHandler.ERROR_PREFIX + ' ' + error
