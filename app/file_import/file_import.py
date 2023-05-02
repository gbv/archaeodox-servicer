import requests
from dpath import util as dp

from app import settings, messages
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.field import error_messages as field_error_messages
from app.file_import.importers import image_importer, worldfile_importer, csv_importer, shapefile_importer


def perform_import(import_object, fylr, logger):
    fylr.acquire_access_token()
    files = __get_files(import_object, fylr)
    __import_files(files, import_object, fylr, logger)

def __get_files(import_object, fylr):
    id = import_object['_id']
    wrapped_object_data = fylr.get_object_by_id('dokumente_extern', id)
    inner_object_data = wrapped_object_data['dokumente_extern']
    nested_files = '_nested:dokumente_extern__dateien'
    
    files = []
    for index, file in enumerate(inner_object_data[nested_files]):
        file_information = file['datei'][0]
        file_name = file_information['original_filename']
        file_extension = file_name.split('.')[-1]
        files.append({
            'name': file_name,
            'url': dp.get(file_information, 'versions/original/download_url'),
            'format_settings': settings.FileImport.FORMATS.get(file_extension, None),
            'detected_format': file_information['extension'],
            'original_index': index
        })

    # Sort files to make sure worldfiles are imported after images
    files.sort(key=__get_sorting_value)
    return files

def __get_sorting_value(file):
    if file['format_settings'] is not None:
        return file['format_settings']['importer']
    else:
        # Import files without recognized format last
        return 'z'

def __import_files(files, import_object, fylr, logger):
    database = __get_field_database(import_object)

    for file in files:
        file['result'] = __import_file(file, import_object, database, fylr, logger)

    files.sort(key=lambda file: file['original_index'])
    results = list(map(lambda file: file['result'], files))
    __create_result_object(results, import_object, fylr)

def __import_file(file, import_object, database, fylr, logger):
    result = {
        'dokument': __get_cloned_asset(file, fylr),
        'dokumententyp': __get_file_type_object(file, fylr)
    }

    try:
        __validate(file, result['dokumententyp'], import_object, database)
        file_data = __get_file_data(file['url'])
        __run_importer(file, file_data, database)
        result['fehlermeldung'] = messages.FileImport.SUCCESS
    except Exception as error:
        logger.debug(f'Import failed for file {file["name"]}', exc_info=True)
        result['fehlermeldung'] = __get_error_message(str(error))
    
    return result

def __get_cloned_asset(file, fylr):
    cloned_asset = fylr.create_asset_from_url(file['name'], file['url'])
    cloned_asset[0]['preferred'] = True
    return cloned_asset

def __get_file_type_object(file, fylr):
    if file['format_settings'] is None:
        return None
    else:
        return fylr.get_object_by_field_value('dateityp', 'name', file['format_settings']['file_type'])

def __validate(file, file_type_object, import_object, database):
    if database is None:
        raise ValueError(messages.FileImport.ERROR_MISSING_CREDENTIALS)
    if not file['name'].startswith(import_object['vorgangsname']):
        raise ValueError(messages.FileImport.ERROR_VORGANG_NOT_IN_FILENAME)
    if file_type_object is None:
        raise ValueError(messages.FileImport.ERROR_UNSUPPORTED_FILE_FORMAT)
    if file['format_settings']['expected_format'] != file['detected_format']:
        raise ValueError(messages.FileImport.ERROR_INVALID_FILE_FORMAT)

def __get_file_data(url):
    response = requests.get(url)
    if response.ok:
        return response.content
    else:
        raise ValueError(response.text)

def __run_importer(file, file_data, database):
    if file['format_settings']['importer'] == 'image':
        image_importer.run(file_data, file['name'], database)
    if file['format_settings']['importer'] == 'worldfile':
        worldfile_importer.run(file_data, file['name'], database)
    if file['format_settings']['importer'] == 'csv':
        csv_importer.run(file_data, file['name'], database)
    if file['format_settings']['importer'] == 'shapefile':
        shapefile_importer.run(file_data, database)

def __get_field_database(import_object):
    if 'vorgangsname' not in import_object or 'passwort' not in import_object:
        return None
    field_hub = FieldHub(
        settings.Couch.HOST_URL,
        settings.FieldHub.TEMPLATE_PROJECT_NAME,
        auth_from_module=True
    )
    db_name = import_object['vorgangsname']
    password = import_object['passwort']
    return FieldDatabase(field_hub, db_name, db_name, password)

def __create_result_object(file_import_results, import_object, fylr):
    fields_data = {
        '_nested:import_ergebnis__dokument': file_import_results
    }
    tags = __get_tags(__is_failed(file_import_results))
    fylr.create_object('import_ergebnis', fields_data, pool=import_object['_pool'], tags=tags)

def __is_failed(file_import_results):
    for result in file_import_results:
        if result['fehlermeldung'] != messages.FileImport.SUCCESS:
            return True
    return False

def __get_tags(failed):
    if failed:
        return [{ '_id': settings.FileImport.FAILURE_TAG_ID }]
    else:
        return [{ '_id': settings.FileImport.SUCCESS_TAG_ID }]

def __get_error_message(error):
    if error == field_error_messages.FIELD_HUB_INVALID_CREDENTIALS:
        error = messages.FileImport.ERROR_INVALID_CREDENTIALS
    
    return messages.FileImport.ERROR_PREFIX + ' ' + error
