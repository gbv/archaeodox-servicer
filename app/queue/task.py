class Task:
    def __init__(self, label, logger, function, *args, **kwargs) -> None:
        self.label = label
        self.logger = logger
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.kwargs['logger'] = logger

    def run(self, on_completed):
        self.logger.info(f'Running task {self.label}.')
        self.function(*self.args, **self.kwargs)
        on_completed()
