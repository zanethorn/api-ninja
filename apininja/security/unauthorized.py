
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
        
    @property
    def roles(self):
        return []
        
    def __bool__(self):
        return False