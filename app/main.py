import time
from datetime import datetime, timezone
from flask import Flask

from app import settings
from app.queue.queue import Queue
from app.queue.task import Task
from app.tasks import valuelists_updater
from app.tasks import handler_factory


app = Flask(__name__)
app.logger.setLevel(settings.Main.LOGGING_LEVEL)


@app.route('/handle-new-object/<string:object_type>/<string:request_id>', methods=['POST'])
def handle(object_type, request_id):
    app.logger.debug(f'Handle new Fylr object of type "{object_type}" with Servicer request ID "{request_id}"')
    try:
        task_label = 'Handle_new_object_' + str(time.time())
        task = Task(
            task_label,
            app.logger,
            handler_factory.run_handler,
            object_type=object_type,
            request_id=request_id
        )
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
    
@app.route('/status', methods=['GET'])
def status():
    return get_status(), 200

task_queue = Queue(app.logger, 3)


def get_status():
    return {
        'running': task_queue.is_running(),
        'queuedTasks': len(task_queue.tasks),
        'completedTasks': task_queue.get_task_count()
    }

app.logger.debug('Started servicer')
