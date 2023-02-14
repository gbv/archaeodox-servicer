import time
from flask import Flask, request as incoming_request

from app import settings
from app.servicer.servicer import Servicer
from app.servicer.task import Task
from app.easydb.database import EasyDB
from app.handlers.easydb_handler import EasyDBHandler
from app.handlers.vorgang_handler import VorgangHandler
from app.field.hub import FieldHub


app = Flask(__name__)


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
    app.logger.debug(f'From edb: {hook}, {object_type}')
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


edb = EasyDB(settings.EasyDB.HOST_URL, app.logger)

servicer = Servicer(app.logger, edb)

servicer.register_handler(Servicer.Hooks.DB_POST_UPDATE_ONE.value,
                          'vorgang',
                          VorgangHandler,
                          delayed=True)

servicer.register_handler(Servicer.Hooks.DB_POST_UPDATE_ONE.value,
                          'dokumente_extern',
                          EasyDBHandler,
                          delayed=False)

app.logger.debug('Started servicer')
app.logger.debug(f'Currently registered handlers: {servicer.handlers}')