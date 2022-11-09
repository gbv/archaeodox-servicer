class EdbHandler:
    def __init__(self, incoming_request):
        self.data = incoming_request.get_json()
    
    def process_request(self):
        return self.data


class DbCreatingHandler(EdbHandler):
    def process_request(self):
        database = self.data['field_database']
        database['password'] = 'geheim'
        return self.data
