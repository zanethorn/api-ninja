
class HttpException(Exception):
    def __init__(self,status,message=None):
        self.status = status
        self.message = message

    def __str__(self):
        return '%s: %s' % (self.status, self.message)