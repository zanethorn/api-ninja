
class UnauthorizedUser():
    @property
    def id(self):
        return ''
        
    @property
    def context(self):
        return self
        
    @property
    def parent(self):
        return root
        
    def __bool__(self):
        return False