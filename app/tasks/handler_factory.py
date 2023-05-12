from datetime import datetime, timezone, timedelta

from app import settings
from app.fylr.database import Fylr
from app.handlers.vorgang_handler import VorgangHandler
from app.handlers.import_handler import ImportHandler

handled_objects_ids = []


def run_handlers(object_type, logger):
    handlers = __create_handlers(object_type, logger)
    for handler in handlers:
        handler.process_request()

def __create_handlers(object_type, logger):
    fylr = Fylr(settings.Fylr.HOST_URL, logger)
    new_objects = __fetch_new_objects(object_type, fylr)
    if new_objects is None:
        return
    
    handlers = []
    for new_object in new_objects:
        id = new_object['_global_object_id']
        if id not in handled_objects_ids:
            handlers.append(__create_handler(object_type, new_object, logger, fylr))
            handled_objects_ids.append(id)
    return handlers

def __fetch_new_objects(object_type, fylr):
    date_format = '%Y-%m-%dT%H:%M:%SZ'
    from_date = datetime.now(timezone.utc) - timedelta(hours=0, minutes=5)
    to_date = datetime.now(timezone.utc)

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
    handler_class = handler_map[object_type]
    return handler_class(object, logger, fylr)
