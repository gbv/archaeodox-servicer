import json


class FylrHandler:
    def __init__(self, data, logger, fylr):
        self.data = data
        self.object_type = self.data['_objecttype']
        self.object_data = self.data[self.object_type]
        self.logger = logger
        self.logger.debug(f'Created handler for object: \n\n{json.dumps(self.data, indent=2)}')
        self.fylr = fylr
    
    def process_request(self, *args, **kwargs):
        self.logger.debug(f'Handler: {self.__class__.__name__}')
        self.logger.debug(f'Full data: {self.data}')
        self.logger.debug(f'Object data {self.object_data}')
        return self.data
