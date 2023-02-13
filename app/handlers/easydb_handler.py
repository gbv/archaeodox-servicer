import json


class EasyDBHandler:
    def __init__(self, incoming_request, logger, easydb):
        self.full_data = incoming_request.get_json()
        self.inner_data = self.full_data['data']
        self.object_type = self.inner_data['_objecttype']
        self.object_data = self.inner_data[self.object_type]
        self.logger = logger
        self.logger.debug(f"Created handler for object: \n\n{json.dumps(self.full_data, indent=2)}")
        self.easydb = easydb
    
    def process_request(self, *args, **kwargs):
        self.logger.debug(f"Handler: {self.__class__.__name__}")
        self.logger.debug(f"Full data: {self.full_data}")
        self.logger.debug(f'Object data {self.object_data}')
        return self.full_data
