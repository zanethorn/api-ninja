class RootUser():
    @property
    def id(self):
        return 'root'
        
    @property
    def context(self):
        return self
        
    @property
    def parent(self):
        return self

    def __bool__(self):
        return True