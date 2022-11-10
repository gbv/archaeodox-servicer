from crypt import methods
from enum import Enum
import http
import requests
import json
import traceback

from flask import Flask, request as incoming_request
from .easydb_client import EasydbClient, EASLiberator
from .wfs_client import WFSClient
from .edbHandler import EdbHandler, DbCreatingHandler
from dpath import util as dp

from .couch import Client as CouchClient
from . import settings

app = Flask(__name__)
edb = EasydbClient("http://easydb-webfrontend", app.logger)

wfs = WFSClient(settings.GEO_SERVER_URL,
                settings.TRANSACTION_ATTRIBUTES,
                settings.OBJECT_TYPE,
                settings.OBJECT_NAMESPACE,
                settings.ATTRIBUTES,
                settings.GEOMETRY,
                app.logger)

app.logger.debug('Started servicer')

class Servicer:
    def __init__(self) -> None:
        self.handlers = {}

    class Hooks(Enum):
        DB_PRE_UPDATE_ONE = 'db_pre_update_one'
        DB_PRE_UPDATE = 'db_pre_update'
        DB_PRE_DELETE_ONE = 'db_pre_delete_one'
        DB_PRE_DELETE = 'db_pre_delete'
        DB_POST_UPDATE_ONE = 'db_post_update_one'
        DB_POST_UPDATE = 'db_post_update'
        DB_POST_DELETE_ONE = 'db_post_delete_one'
        DB_POST_DELETE = 'db_post_delete'


    
    def handle_edb_hook(self, hook, object_type, incoming_request):
        handler = self.handlers[(hook, object_type)](incoming_request, app.logger)
        return handler.process_request()

    def register_handler(self, hook, object_type, handler_class):
        self.handlers[(hook, object_type)] = handler_class



@app.route('/<string:hook>/<string:object_type>', methods=['POST'])
def generic_edb_hook(hook, object_type):
    app.logger.debug(f"From edb: {hook}, {object_type}")
    try:
        return servicer.handle_edb_hook(hook, object_type, incoming_request)
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500


def get_wfs_id(item_type, id, token):
    result, code = edb.get_item(item_type, id, token=token)
    app.logger.debug("Got items: " + json.dumps(result, indent=2))
    return dp.get(result, [item_type, "feature_id"])




servicer = Servicer()
servicer.register_handler(Servicer.Hooks.DB_PRE_UPDATE_ONE.value, 'field_database', DbCreatingHandler)
servicer.register_handler(Servicer.Hooks.DB_PRE_UPDATE_ONE.value, 'csv_dump', EdbHandler)

app.logger.debug(f'Currently registered handlers: {servicer.handlers}')