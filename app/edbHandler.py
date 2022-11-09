class EdbHandler:
    def __init__(self, incoming_request, logger):
        self.data = incoming_request.get_json()['data']
        self.logger = logger
    
    def process_request(self):
        self.logger.debug(f'Handling {self.data}')
        return self.data


class DbCreatingHandler(EdbHandler):
    def process_request(self):
        self.logger.debug(f'Handling {self.data}')
        
        database = self.data['field_database']
        database['password'] = 'geheim'
        return self.data
