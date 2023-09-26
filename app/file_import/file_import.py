import re
from dpath import util as dp

from app import settings, messages
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.field import error_messages as field_error_messages
from app.file_import.importers import image_importer, worldfile_importer, csv_importer, shapefile_importer, fylr_importer


def perform_import(import_object, fylr, logger):
    fylr.acquire_access_token()
    files = __get_files(import_object, fylr)
    results = __import_files(files, import_object, fylr, logger)
    __create_result_object(results, import_object, fylr)
    __delete_import_object(import_object, fylr)

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
        file_url = dp.get(file_information, 'versions/original/url')
        format_settings = settings.FileImport.FORMATS.get(file_extension, None)
        import_settings = __get_import_settings(file_name)
        files.append({
            'name': file_name,
            'data': fylr.download_asset(file_url),
            'mimetype': dp.get(file_information, 'versions/original/technical_metadata/mime_type'),
            'user_name': dp.get(file_information, 'upload_user/user/_generated_displayname'),
            'format_settings': format_settings,
            'importers': __get_importers(format_settings, import_settings),
            'document_type_concept_id': __get_document_type_concept_id(import_settings),
            'detected_format': file_information['technical_metadata']['file_type_extension'],
            'original_index': index
        })
    
    for file in __get_image_files(files):
        file['has_worldfile'] = __has_worldfile(file, files)

    # Sort files to make sure worldfiles are imported after images
    files.sort(key=__get_sorting_value)
    return files

def __get_import_settings(file_name):
    document_type_code = __get_document_type_code(file_name)
    if document_type_code is None:
        return None
    elif re.match(r'^[A-Z]{1,3}\d+$', document_type_code):
        document_type_code = re.search(r'^[A-Z]{1,3}', document_type_code)[0]
        import_settings = settings.FileImport.IMPORT_MAPPING.get(document_type_code, None)
        if import_settings is not None and import_settings.get('numbered', False) == True:
            return import_settings
        else:
            return None
    else:
        return settings.FileImport.IMPORT_MAPPING.get(document_type_code, None)

def __get_document_type_code(file_name):
    file_name_segments = file_name.split('_')
    if len(file_name_segments) < 2:
        return None
    return file_name_segments[1]

def __get_importers(format_settings, import_settings):
    importers = []
    if import_settings is not None:
        for importer, file_formats in import_settings['importers'].items():
            if format_settings['file_type'] in file_formats:
                importers.append(importer)
    return importers

def __get_image_files(files):
    return filter(lambda file: 'image' in file['importers'], files)

def __has_worldfile(file, files):
    base_name = __get_base_name(file['name'])
    worldfiles = filter(lambda file: 'worldfile' in file['importers'], files)
    worldfile_names = map(lambda file: file['name'], worldfiles)
    for worldfile_name in worldfile_names:
       if __get_base_name(worldfile_name) == base_name:
           return True
    return False

def __get_base_name(file_name):
    extension = file_name.split('.')[-1]
    return file_name.replace('.' + extension, '')

def __get_document_type_concept_id(import_settings):
    if import_settings is None:
        return None;
    else:
        return import_settings['document_type_concept_id']

def __get_sorting_value(file):
    sorting_value = len(settings.FileImport.ORDER)
    for importer in file['importers']:
        sorting_value = min(sorting_value, settings.FileImport.ORDER.index(importer))
    return sorting_value

def __import_files(files, import_object, fylr, logger):
    database = __get_field_database(import_object)

    for file in files:
        file['result'] = __import_file(file, import_object, database, fylr, logger)

    files.sort(key=lambda file: file['original_index'])
    return list(map(lambda file: file['result'], files))

def __import_file(file, import_object, database, fylr, logger):
    result = {
        'dokument': __get_cloned_asset(file, fylr),
        'dokumententyp': __get_file_type_object(file, fylr)
    }

    try:
        __validate(file, result['dokumententyp'], import_object, database)
        for importer in file['importers']:
            __run_importer(importer, file, file['data'], import_object, database, fylr)
        result['fehlermeldung'] = messages.FileImport.SUCCESS
    except Exception as error:
        logger.debug(f'Import failed for file {file["name"]}', exc_info=True)
        result['fehlermeldung'] = __get_error_message(str(error))
    
    return result

def __get_cloned_asset(file, fylr):
    cloned_asset = fylr.create_asset(file['name'], file['data'], file['mimetype'])
    cloned_asset[0]['preferred'] = True
    return cloned_asset

def __get_file_type_object(file, fylr):
    if file['format_settings'] is None:
        return None
    else:
        return fylr.get_object_by_field_value('import_ergebnis_dateityp', 'name', file['format_settings']['file_type'])

def __validate(file, file_type_object, import_object, database):
    if database is None:
        raise ValueError(messages.FileImport.ERROR_MISSING_CREDENTIALS)
    if not file['name'].startswith(import_object['vorgangsname']):
        raise ValueError(messages.FileImport.ERROR_VORGANG_NOT_IN_FILENAME)
    if file_type_object is None:
        raise ValueError(messages.FileImport.ERROR_UNSUPPORTED_FILE_FORMAT)
    if file['format_settings']['expected_format'] != file['detected_format']:
        raise ValueError(messages.FileImport.ERROR_INVALID_FILE_FORMAT + ' ' + file['detected_format'])
    if file['document_type_concept_id'] is None:
        raise ValueError(messages.FileImport.ERROR_DOCUMENT_TYPE_CODE_NOT_FOUND)
    if len(file['importers']) == 0:
        raise ValueError(messages.FileImport.ERROR_UNSUPPORTED_FILE_FORMAT_FOR_DOCUMENT_TYPE)

def __run_importer(importer, file, file_data, import_object, database, fylr):
    if importer == 'image':
        image_importer.run(file_data, file['name'], file['has_worldfile'], database)
    elif importer == 'worldfile':
        worldfile_importer.run(file_data, file['name'], database)
    elif importer == 'csv':
        csv_importer.run(file_data, file['name'], database)
    elif importer == 'shapefile':
        shapefile_importer.run(file_data, database)
    elif importer == 'fylr':
        fylr_importer.run(__get_cloned_asset(file, fylr), file['document_type_concept_id'], file['user_name'],
                          file['name'], import_object['_pool'], fylr)

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

def __delete_import_object(import_object, fylr):
    fylr.delete_object('dokumente_extern', import_object['_id'])

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
