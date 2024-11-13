import time
import threading
import json


class Queue():
    def __init__(self, logger, delay) -> None:
        self.tasks = []
        self.logger = logger
        self.delay = delay
        threading.Thread(name='task_trigger', target=self._trigger_tasks).start()

    def append(self, task):
        time_stamp = time.time()
        self.tasks.append((time_stamp, task))
        self.logger.debug(f'Enqueued {task}.')

    def is_running(self):
        task_runner_threads = list(filter(lambda thread: thread.name == 'task_runner', threading.enumerate()))
        return len(task_runner_threads) > 0

    def get_task_count(self):
        try:
            with open('queueState.json') as file:
                state = json.loads(file.read())
                return state['taskCount']
        except Exception:
            return 0
        
    def _trigger_tasks(self):
        while True:
            self.__run_next()
            time.sleep(1)
    
    def __run_next(self):
        if self.is_running():
            return 
        
        def sufficiently_aged(time_task_pair):
            now = time.time()
            max_time_stamp = now - self.delay
            return time_task_pair[0] <= max_time_stamp

        matured_tasks = list(filter(sufficiently_aged, self.tasks))

        if matured_tasks:
            _, next_task = self.tasks.pop(0)
            threading.Thread(name='task_runner', target=next_task.run, args=[self.__update_task_count]).start()

    def __update_task_count(self):
        current_task_count = self.get_task_count()
        self.__write_task_count(current_task_count + 1)

    def __write_task_count(self, task_count):
        with open('queueState.json', 'w') as file:
            state = { 'taskCount': task_count }
            file.write(json.dumps(state))
