from app.handlers.fylr_handler import FylrHandler
from app.file_import.file_import import perform_import


class ImportHandler(FylrHandler):
    def process_request(self, *args, **kwargs):
        perform_import(self.object_data, self.fylr, self.logger)
        return self.full_data
