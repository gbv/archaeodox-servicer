import traceback


class DummyLogger:

    def debug(self, *args, **kwargs):
        self.__log('DEBUG:', args)
        self.__log_exceptions(kwargs)
    
    def info(self, *args, **kwargs):
        self.__log('INFO:', args)
        self.__log_exceptions(kwargs)
    
    def warning(self, *args, **kwargs):
        self.__log('WARNING:', args)
        self.__log_exceptions(kwargs)
    
    def error(self, *args, **kwargs):
        self.__log('ERROR:', args)
        self.__log_exceptions(kwargs)
    
    def critical(self, *args, **kwargs):
        self.__log('CRITICAL:', args)
        self.__log_exceptions(kwargs)

    def __log(self, prefix, *args):
        texts = map(str, *args)
        texts = [prefix] + list(texts)
        print('\n'.join(texts))

    def __log_exceptions(self, kwargs):
        if 'exc_info' in kwargs and kwargs['exc_info']:
            traceback.print_exc()