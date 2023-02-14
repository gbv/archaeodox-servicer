import mimetypes
from dpath import util as dp

from app import settings
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.handlers.easydb_handler import EasyDBHandler


class FileImportingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        self.easydb.acquire_session()
        files = self.__get_files(self.object_data, self.object_type)
        self.__import_files(files)
    
        return self.full_data

    def __get_files(self, object_data, object_type):
        id = object_data['_id']
        wrapped_object_data = self.easydb.get_object_by_id(object_type, id)
        inner_object_data = wrapped_object_data[object_type]
        nested_files = '_nested:' + object_type + '__dateien'
        
        files = []
        for file in inner_object_data[nested_files]:
            file_information = file['datei'][0]
            file_name = file_information['original_filename']
            mime_type = mimetypes.guess_type(file_name)[0]
            files.append({
                'name': file_name,
                'url': dp.get(file_information, 'versions/original/download_url'),
                'mime_type': mime_type,
                'easydb_object': file['datei']
            })
        return files

    def __import_files(self, files):
        database = self.__create_field_database()
        results = []

        for file in files:
            result = self.__import_file(file, database)
            results.append(result)

        self.__create_result_object(results)

    def __import_file(self, file, database):
        result = { 'dokument': file['easydb_object'] }

        try:
            if database is None:
                raise ValueError(settings.FileImportingHandler.ERROR_MISSING_CREDENTIALS_MESSAGE)

            if file['mime_type'] in settings.FileImportingHandler.IMAGE_IMPORT_MIME_TYPES:
                self.logger.debug(f'Image import: {file["name"]}')
                database.ingest_image_from_url(file['url'], file['name'])
            if file['mime_type'] in settings.FileImportingHandler.CSV_IMPORT_MIME_TYPES:
                self.logger.debug(f'CSV import: {file["name"]}')
            if file['mime_type'] in settings.FileImportingHandler.SHAPEFILE_IMPORT_MIME_TYPES:
                self.logger.debug(f'Shapefile import: {file["name"]}')
            result['fehlermeldung'] = settings.FileImportingHandler.SUCCESS_MESSAGE
        except Exception as error:
            result['fehlermeldung'] = str(error)
        
        return result

    def __create_field_database(self):
        field_hub = FieldHub(
            settings.Couch.HOST_URL,
            settings.FieldHub.TEMPLATE_PROJECT_NAME,
            auth_from_module=True
        )
        if 'db_name' not in self.object_data or 'passwort' not in self.object_data:
            return None
        db_name = self.object_data['db_name']
        password = self.object_data['passwort']
        return FieldDatabase(field_hub, db_name, password)

    def __create_result_object(self, file_import_results):
        fields_data = {
            '_nested:import_ergebnis__dokument': file_import_results
        }
        tags = self.__get_tags(self.__is_failed(file_import_results))
        self.easydb.create_object('import_ergebnis', fields_data, pool=self.object_data['_pool'], tags=tags)

    def __is_failed(self, file_import_results):
        for result in file_import_results:
            if result['fehlermeldung'] != settings.FileImportingHandler.SUCCESS_MESSAGE:
                return True
        return False

    def __get_tags(self, failed):
        if failed:
            return [{ '_id': settings.FileImportingHandler.FAILURE_TAG_ID }]
        else:
            return [{ '_id': settings.FileImportingHandler.SUCCESS_TAG_ID }]