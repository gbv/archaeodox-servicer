class EdbHandler:
    def __init__(self, incoming_request, logger):
        self.full_data = incoming_request.get_json()
        self.inner_data = self.full_data['data']
        self.object_type = self.inner_data['_objecttype']
        self.object_data = self.inner_data[self.object_type]
        self.logger = logger
    
    def process_request(self):
        self.logger.debug(f'Handling {self.object_data}')
        return self.full_data


class DbCreatingHandler(EdbHandler):
    def process_request(self):
        self.logger.debug(f'Handling {self.inner_data}')
        
        database = self.object_data
        database['password'] = 'geheim'
        return self.full_data
