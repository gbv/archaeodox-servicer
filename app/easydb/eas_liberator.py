import zipfile, tempfile, shutil, glob
from os.path import join

from app.easydb.dummy_logger import DummyLogger


class EASLiberator:
    def __init__(self, base_path='', base_url = '', logger=None):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logger = logger if not logger is None else DummyLogger()
        self.base_path = base_path
        self.base_url = base_url
        
    def clean_up(self):
        try:
            self.temp_dir.cleanup()
        except Exception as e:
            self.logger.error(str(e))

    def extract_and_copy(self, source, dest, *extensions):
        with zipfile.ZipFile(source, 'r') as archive:
            archive.extractall(self.temp_dir.name)
        report = []
        to_copy = []
        for extension in list(extensions):
            path = f'{self.temp_dir.name}/*.{extension}'
            to_copy += glob.glob(path)
        
        for found_file in to_copy:
            try:
                shutil.copy(found_file, dest)  
                log = f'Copied {found_file} to {dest}/'
                self.logger.info(f'Copied {found_file} to {dest}/')
                report.append(log)
            except Exception as e:
                self.logger.error(str(e))
                report.append(str(e))
        self.clean_up()
        return '\n'.join(report)

    def grab_from_url(self, url, dest, *extensions):
        file_name = url.replace(self.base_url, '')
        file_name = file_name.replace('/application/zip', '')

        file_name = join(self.base_path, file_name)

        return self.extract_and_copy(file_name, dest, *extensions)
