
class EdbHandler:
    
    def process_request(self, hook, object_type, incoming_request):
        return incoming_request.get_json()