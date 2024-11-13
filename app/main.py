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


@app.route('/handle-new-objects/<string:object_type>', methods=['POST'])
def handle(object_type):
    app.logger.debug(f'Handle new Fylr objects of type: {object_type}')
    try:
        task_label = 'Handle_new_objects_' + str(time.time())
        task = Task(
            task_label,
            app.logger,
            handler_factory.run_handlers,
            object_type=object_type,
            task_creation_time=datetime.now(timezone.utc)
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

task_queue = Queue(app.logger, 4)


def get_status():
    return {
        'running': task_queue.is_running(),
        'queuedTasks': len(task_queue.tasks),
        'completedTasks': task_queue.get_task_count()
    }

app.logger.debug('Started servicer')
