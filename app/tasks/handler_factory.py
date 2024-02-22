from datetime import datetime, timedelta

from app import settings
from app.fylr.database import Fylr
from app.handlers.vorgang_handler import VorgangHandler
from app.handlers.import_handler import ImportHandler

handled_objects_ids = []
date_format = '%Y-%m-%dT%H:%M:%S%z'
time_margin = 5 # Minutes


def run_handlers(object_type, task_creation_time, logger):
    handlers = __create_handlers(object_type, task_creation_time, logger)
    for handler in handlers:
        handler.process_request()

def __create_handlers(object_type, task_creation_time, logger):
    fylr = Fylr(settings.Fylr.HOST_URL, logger)
    new_objects = __fetch_new_objects(object_type, task_creation_time, fylr)
    if new_objects is None:
        return
    
    handlers = []
    for new_object in new_objects:
        id = new_object['_global_object_id']
        if id not in handled_objects_ids and __is_newly_created(new_object, task_creation_time):
            handlers.append(__create_handler(object_type, new_object, logger, fylr))
            handled_objects_ids.append(id)
    return handlers

def __fetch_new_objects(object_type, task_creation_time, fylr):
    delta = timedelta(hours=0, minutes=time_margin)
    from_date = task_creation_time - delta
    to_date = task_creation_time + delta

    fylr.acquire_access_token()

    return fylr.changelog_search(
        object_type,
        from_date.strftime(date_format),
        to_date.strftime(date_format),
        'INSERT'
    )

def __create_handler(object_type, object, logger, fylr):
    handler_map = {
        'vorgang': VorgangHandler,
        'dokumente_extern': ImportHandler
    }
    del object['_score']
    handler_class = handler_map[object_type]
    return handler_class(object, logger, fylr)

def __is_newly_created(object, task_creation_time):
    object_creation_time = datetime.strptime(object['_created'], date_format)
    min_creation_time = task_creation_time - timedelta(hours=0, minutes=time_margin)
    return object_creation_time > min_creation_time
