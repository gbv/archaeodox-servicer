import requests

from app import settings


class Geoserver:
    def __init__(self):
        self.workspace = settings.Geoserver.WORKSPACE_NAME
        self.url = f'{settings.Geoserver.URL}/rest/workspaces/{self.workspace}'
        self.auth = (settings.Geoserver.USER_NAME, settings.Geoserver.PASSWORD)

    def create_or_update_wms_layer(self, name, image_data):
        if self.__get_coverage_store(name) is None:
            self.__create_coverage_store(name)
        self.__upload_image_to_converage_store(name, image_data)

    def __get_coverage_store(self, name):
        url = f'{self.url}/coveragestores/{name}'
        response = requests.get(url, auth=self.auth)
        if response.status_code == 404:
            return None
        elif not response.ok:
            raise ValueError(f'{response.status_code} {response.text}')
        else:
            return response.json()

    def __create_coverage_store(self, store_name):
        url = f'{self.url}/coveragestores'
        headers = { 'Content-type': 'application/xml' }
        data = f'''
           <coverageStore>
                <name>{store_name}</name>
                <workspace>{self.workspace}</workspace>
                <enabled>true</enabled>
            </coverageStore>
        '''

        response = requests.post(url, auth=self.auth, data=data, headers=headers)
        if not response.ok:
            raise ValueError(f'{response.status_code} {response.text}')
        
    def __upload_image_to_converage_store(self, store_name, image_data):
        url = f'{self.url}/coveragestores/{store_name}/file.geotiff'
        headers = { 'Content-type': 'image/tiff' }

        response = requests.put(url, auth=self.auth, data=image_data, headers=headers)
        if not response.ok:
            raise ValueError(f'{response.status_code} {response.text}')
