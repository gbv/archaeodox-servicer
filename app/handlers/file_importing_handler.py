from app.handlers.easydb_handler import EasyDBHandler
from app.file_import.file_import import perform_import


class FileImportingHandler(EasyDBHandler):
    def process_request(self, *args, **kwargs):
        perform_import(self.object_data, self.easydb)
        return self.full_data
