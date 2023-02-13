from app import settings
from app.field.database import FieldDatabase
from app.field.hub import FieldHub
from app.handlers.easydb_handler import EasyDBHandler


class FileImportingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        hub = FieldHub(settings.Couch.HOST_URL,
                       settings.FieldHub.TEMPLATE_PROJECT_NAME,
                       auth_from_module=True)
        password = self.object_data['password']

        self.easydb.acquire_session()
        files = self.easydb.get_files_from_object(self.object_data, self.object_type)
        self.logger.debug(files)

        for file in files:
            # TODO Read db name from image file
            db_name = ''
            database = FieldDatabase(hub, db_name, password)

            if file['mime_type'] in settings.EdbHandlers.IMAGE_IMPORT_MIME_TYPES:
                self.logger.debug(f'Image import: {file["name"]}')
                database.ingest_image_from_url(file['url'], file['name'])
            if file['mime_type'] in settings.EdbHandlers.CSV_IMPORT_MIME_TYPES:
                self.logger.debug(f'CSV import: {file["name"]}')
            if file['mime_type'] in settings.EdbHandlers.SHAPEFILE_IMPORT_MIME_TYPES:
                self.logger.debug(f'Shapefile import: {file["name"]}')
    
        return self.full_data
