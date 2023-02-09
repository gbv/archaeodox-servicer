import time
from enum import Enum

from app.servicer.queue import Queue
from app.servicer.task import Task


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
