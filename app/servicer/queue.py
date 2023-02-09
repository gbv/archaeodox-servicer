import time


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
