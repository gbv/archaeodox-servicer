import time
import threading


class Queue():
    def __init__(self, logger, delay) -> None:
        self.tasks = []
        self.logger = logger
        self.delay = delay

    def append(self, task):
        time_stamp = time.time()
        self.tasks.append((time_stamp, task))
        self.logger.debug(f'Enqueued {task}.')

    def run_next(self):
        if self.is_running():
            return f'Already running.'
        
        def sufficiently_aged(time_task_pair):
            now = time.time()
            max_time_stamp = now - self.delay
            return time_task_pair[0] <= max_time_stamp

        matured_tasks = list(filter(sufficiently_aged, self.tasks))

        if matured_tasks:
            _, next_task = self.tasks.pop(0)
            threading.Thread(name='task_runner', target=next_task.run, args=[self.__update_task_count]).start()
            return f'Starting task: {next_task.label}'
        else:
            return 'No scheduled tasks.'

    def is_running(self):
        task_runner_threads = list(filter(lambda thread: thread.name == 'task_runner', threading.enumerate()))
        return len(task_runner_threads) > 0

    def get_task_count(self):
        try:
            with open('taskCount') as file:
                return int(file.read())
        except Exception:
            return 0

    def __update_task_count(self):
        current_task_count = self.get_task_count()
        self.__write_task_count(current_task_count + 1)

    def __write_task_count(self, task_count):
        with open('taskCount', 'w') as file:
            file.write(str(task_count))
