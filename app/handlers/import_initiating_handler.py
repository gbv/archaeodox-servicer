from app import settings
from app.handlers.easydb_handler import EasyDBHandler


class ImportInitiatingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        result = self.object_data[settings.Easydb.IMPORT_RESULT_FIELD]
        self.logger.debug(self.object_data)
        if not result:
            self.object_data[settings.Easydb.IMPORT_RESULT_FIELD] = settings.Easydb.IMPORT_REGISTRATION_MESSAGE
        
        return self.full_data
