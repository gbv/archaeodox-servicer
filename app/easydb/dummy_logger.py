class DummyLogger:
    def log(self, prefix, *args):
        texts = map(str, *args)
        texts = [prefix] + list(texts)
        print('\n'.join(texts))

    def debug(self, *args):
        self.log('DEBUG:', args)
    
    def info(self, *args):
        self.log('INFO:', args)
    
    def warning(self, *args):
        self.log('WARNING:', args)
    
    def error(self, *args):
        self.log('ERROR:', args)
    
    def critical(self, *args):
        self.log('CRITICAL:', args)
