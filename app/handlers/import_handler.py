from app.handlers.easydb_handler import EasyDBHandler
from app.file_import.file_import import perform_import


class ImportHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        perform_import(self.object_data, self.easydb, self.logger)
        return self.full_data
