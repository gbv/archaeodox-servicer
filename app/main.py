import time
from flask import Flask, request as incoming_request

from app import settings
from app.queue.queue import Queue
from app.queue.task import Task
from app.fylr.database import Fylr
from app.handlers.vorgang_handler import VorgangHandler
from app.handlers.import_handler import ImportHandler
from app.tasks import valuelists_updater
from app.tasks import handler_factory


app = Flask(__name__)
app.logger.setLevel(settings.Main.LOGGING_LEVEL)


@app.route('/run-delayed', methods=['GET'])
def run_delayed():
    try:
        task_label = task_queue.pop()
        return task_label, 200
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500

@app.route('/handle-new-objects/<string:object_type>', methods=['POST'])
def handle(object_type):
    app.logger.debug(f'Handle new Fylr objects of type: {object_type}')
    try:
        task_label = 'Handle_new_objects_' + str(time.time())
        task = Task(task_label, app.logger, handler_factory.run_handlers, object_type=object_type)
        task_queue.append(task)
        return task_label, 200
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500

@app.route('/update-valuelists', methods=['POST'])
def update_valuelists():
    try:
        task_label = 'Update_valuelists_' + str(time.time())
        task = Task(task_label, app.logger, valuelists_updater.update)
        task_queue.append(task)
        return task_label, 200
    except Exception as exception:
        app.logger.exception(exception)
        return str(exception), 500

task_queue = Queue(app.logger, 4)


app.logger.debug('Started servicer')
