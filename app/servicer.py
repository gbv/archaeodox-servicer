from crypt import methods
from enum import Enum
import http
import requests
import json
import traceback
import time

from flask import Flask, request as incoming_request
from .utils.easydb_client import EasydbClient, EASLiberator
from .utils.wfs_client import WFSClient
from .utils.edbHandlers import EdbHandler, DbCreatingHandler, FileImportingHandler, ImportInitiatingHandler
from .utils.field_client import FieldHub

from dpath import util as dp

from . import settings

app = Flask(__name__)

wfs = WFSClient(settings.WFS.GEO_SERVER_URL,
                settings.WFS.TRANSACTION_ATTRIBUTES,
                settings.WFS.OBJECT_TYPE,
                settings.WFS.OBJECT_NAMESPACE,
                settings.WFS.ATTRIBUTES,
                settings.WFS.GEOMETRY,
                app.logger)

app.logger.debug('Started servicer')

class Queue():
    def __init__(self, logger, delay) -> None:
        self.tasks = []
        self.logger = logger
        self.delay = delay

    def append(self, task):
        time_stamp = time.time()
        self.tasks.append((time_stamp, task))
        self.logger.debug(f'Enqueued {task}.')

    def pop(self):
        
        def sufficiently_aged(time_task_pair):
            now = time.time()
            max_time_stamp = now - self.delay
            return time_task_pair[0] <= max_time_stamp

        matured_tasks = list(filter(sufficiently_aged, self.tasks))

        if matured_tasks:
            time_stamp, next_task = self.tasks.pop(0)
            self.logger.debug(f'Popped Task: {next_task.label}')
            next_task.run()
            return next_task.label
        else:
            return 'No scheduled tasks.'

class Task:
    def __init__(self, label, logger, function, *args, **kwargs) -> None:
        self.label = label
        self.logger = logger
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.kwargs['logger'] = logger

    def run(self):
        self.logger.info(f"Running task {self.label}.")
        return self.function(*self.args, **self.kwargs)


class Servicer:
    def __init__(self, logger, edb_client) -> None:
        self.handlers = {}
        self.logger = logger
        self.delayed_task_queue = Queue(logger, 4)
        self.edb_client = edb_client

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
        handler_class, delayed = self.handlers[(hook, object_type)]
        handler = handler_class(incoming_request, app.logger, self.edb_client)
        if delayed:
            task_label = '_'.join((hook, object_type, str(time.time())))
            task = Task(task_label, self.logger, handler.process_request)
            self.delayed_task_queue.append(task)
            self.logger.debug(self.delayed_task_queue.tasks)
            return f'Enqueued {task_label}', 200
        else:
            return handler.process_request()

    def register_handler(self, hook, object_type, handler_class, delayed=False):
        self.handlers[(hook, object_type)] = (handler_class, delayed)



@app.route('/run-delayed', methods=['GET'])
def run_delayed():
    try:
        task_label = servicer.delayed_task_queue.pop()
        return task_label, 200
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500

@app.route('/<string:hook>/<string:object_type>', methods=['POST'])
def generic_edb_hook(hook, object_type):
    app.logger.debug(f"From edb: {hook}, {object_type}")
    try:
        return servicer.handle_edb_hook(hook, object_type, incoming_request)
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500

@app.route('/update-valuelists', methods=['POST'])
def update_valuelists():
    def actually_update(logger, *args, **kwargs):
        field_hub = FieldHub(settings.Couch.HOST_URL,
                    settings.FieldHub.TEMPLATE_PROJECT_NAME,
                    auth_from_module=True,
                    logger=logger)
        field_hub.update_valuelists()
    try:
        task_label = 'Update_valuelists_' + str(time.time())
        task = Task(task_label, servicer.logger, actually_update)
        servicer.delayed_task_queue.append(task)
        return task_label, 200
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500


def get_wfs_id(item_type, id, token):
    result, code = edb.get_item(item_type, id, token=token)
    app.logger.debug("Got items: " + json.dumps(result, indent=2))
    return dp.get(result, [item_type, "feature_id"])

#
# The actual app works below here
#

edb = EasydbClient(settings.Easydb.HOST_URL, app.logger)

servicer = Servicer(app.logger, edb)

servicer.register_handler(Servicer.Hooks.DB_POST_UPDATE_ONE.value,
                          'vorgang',
                          EdbHandler,
                          delayed=False)

app.logger.debug(f'Currently registered handlers: {servicer.handlers}')