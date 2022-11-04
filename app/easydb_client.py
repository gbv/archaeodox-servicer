import json, requests
import zipfile, tempfile, shutil, glob
from os.path import join
from . import credentials


class DummyLogger:
    def log(self, prefix, *args):
        texts = map(str, *args)
        texts = [prefix] + list(texts)
        print('\n'.join(texts))

    def debug(self, *args):
        self.log('DEBUG:', args)
    
    def info(self, *args):
        self.log('INFO:', args)
    
    def warning(self, *args):
        self.log('WARNING:', args)
    
    def error(self, *args):
        self.log('ERROR:', args)
    
    def critical(self, *args):
        self.log('CRITICAL:', args)
    


class EasydbClient:
    API_PATH = "api/v1"

    

    def __init__(self, url, logger):
        self.url = url
        self.session_url = join(url,
                                     EasydbClient.API_PATH,
                                     "session")
        self.search_url = join(url,
                                    EasydbClient.API_PATH,
                                    "search")
        self.session_auth_url = join(url,
                                          EasydbClient.API_PATH,
                                          "session",
                                          "authenticate")
        self.db_url = join(url,
                                EasydbClient.API_PATH,
                                "db")
        self.logger = logger
        #self.acquire_session()

    def acquire_session(self):
        session_response = requests.get(self.session_url)
        if session_response.status_code == 200:
            session_info = json.loads(session_response.content)
            self.session_token = session_info['token']

            params = {"token": self.session_token,
                      "login": credentials.USER_NAME,
                      "password": credentials.PASSWORD}
            auth_response = requests.post(self.session_auth_url,
                                          params=params)
            self.logger.debug(f"Attempting auth: {params}")
            if not auth_response.status_code == 200:
                raise ValueError(f"Failed to authenticate: {auth_response.content}")
        else:
            raise ValueError(f"Failed to acquire session from {self.session_url}")

    def get_item(self, item_type, id, id_field="_id", pretty=0, token=None):
        search = [{"type": "in",
                   "bool": "must",
                   "fields": [".".join((item_type, id_field))],
                   "in": [id]
                   }]
        token = token if token is not None else self.session_token
        params = {"token": token}

        get_url = join(self.db_url,
                            item_type,
                            "_all_fields",
                            str(id))

        response = requests.get(get_url, params=params)

        if response.status_code == 200:
            result = json.loads(response.content)[0]
        else:
            result = {}
        return result, response.status_code


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
    


if __name__ == '__main__':
    l = EASLiberator(base_url='https://hekate.gbv.de/eas/partitions-inline/1/',
                     base_path='/srv/easydb/eas/lib/assets/orig')
    l.grab_from_url('https://hekate.gbv.de/eas/partitions-inline/1/0/0/27/2211a8827b819939d7d6643eff2adcc4eb58b203/application/zip')