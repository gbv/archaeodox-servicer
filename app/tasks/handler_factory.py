from time import sleep

from app import settings
from app.fylr.database import Fylr
from app.handlers.vorgang_handler import VorgangHandler
from app.handlers.import_handler import ImportHandler

MAX_WAITING_TIME = 120
LOOP_WAITING_TIME = 5

def run_handler(object_type, request_id, logger):
    handler = __create_handler(object_type, request_id, logger)
    if handler is not None:
        handler.process_request()

def __create_handler(object_type, request_id, logger):
    fylr = Fylr(settings.Fylr.HOST_URL, logger)
    fylr.acquire_access_token()

    new_object = __fetch_object(object_type, request_id, fylr, logger)
    if new_object is not None:
        return __build_handler_object(object_type, new_object, fylr, logger)

def __fetch_object(object_type, request_id, fylr, logger, waiting_time = 0):
    object = fylr.get_object_by_field_values(object_type, { 'servicer_request_id': request_id })
    if object is not None:
        return object
    elif waiting_time < MAX_WAITING_TIME:
        sleep(LOOP_WAITING_TIME)
        return __fetch_object(object_type, request_id, fylr, logger, waiting_time + LOOP_WAITING_TIME)
    else:
        logger.warn(f'Max waiting time exceeded for object of type {object_type} with Servicer request ID {request_id}')
        return None

def __build_handler_object(object_type, object, fylr, logger):
    handler_map = {
        'vorgang': VorgangHandler,
        'dokumente_extern': ImportHandler
    }
    handler_class = handler_map[object_type]
    return handler_class(object, logger, fylr)
