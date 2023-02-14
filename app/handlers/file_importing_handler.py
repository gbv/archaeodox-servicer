from app import settings
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.handlers.easydb_handler import EasyDBHandler


class FileImportingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        db_name = self.object_data['db_name']
        password = self.object_data['passwort']

        self.easydb.acquire_session()
        files = self.easydb.get_files_from_object(self.object_data, self.object_type)

        results = []
        failed = False

        for file in files:
            result = { 'dokument': file['easydb_object'] }
            database = FieldDatabase(hub, db_name, password)

            try:
                if file['mime_type'] in settings.EdbHandlers.IMAGE_IMPORT_MIME_TYPES:
                    self.logger.debug(f'Image import: {file["name"]}')
                    database.ingest_image_from_url(file['url'], file['name'])
                if file['mime_type'] in settings.EdbHandlers.CSV_IMPORT_MIME_TYPES:
                    self.logger.debug(f'CSV import: {file["name"]}')
                if file['mime_type'] in settings.EdbHandlers.SHAPEFILE_IMPORT_MIME_TYPES:
                    self.logger.debug(f'Shapefile import: {file["name"]}')
                result['fehlermeldung'] = 'OK'
            except Exception as error:
                result['fehlermeldung'] = str(error)
                failed = True
            results.append(result)

        self.__create_result_object(results, failed)
    
        return self.full_data

    def __create_result_object(self, file_import_results, failed):
        fields_data = {
            '_nested:import_ergebnis__dokument': file_import_results
        }
        tags = self.__get_tags(failed)
        self.easydb.create_object('import_ergebnis', fields_data, pool=self.object_data['_pool'], tags=tags)


    def __get_tags(self, failed):
        if failed:
            return [{ '_id': settings.EdbHandlers.IMPORT_FAILURE_TAG_ID }]
        else:
            return [{ '_id': settings.EdbHandlers.IMPORT_SUCCESS_TAG_ID }]
