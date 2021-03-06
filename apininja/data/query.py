﻿
from apininja.helpers import *

class DataQuery():
    

    def __init__(self,container,context,cursor,**options):
        self.container = container
        self.context = context
        self.cursor = cursor
        
        self.skip = 0
        self.limit = None
        self.selector = None
        
        for k,v in options.items():
            setattr(self,k,v)
        self.options = options
        self.skipped = 0
        self.taken = 0
        
        if self.selector is None:
            self.selector = lambda d: self.container.make_item(d)
        
    def _skip(self):
        while True:
            item = self._get_next_item()
            if item.can_read(self.context):
                self.skipped += 1
                return
            # else:
                # log.debug('skipping %s because I can\'t read it',item)
        
    def _take(self):
        while True:
            item = self._get_next_item()
            if item.can_read(self.context):
                self.taken += 1
                return item
            # else:
                # log.debug('skipping %s because I can\'t read it',item)
            
                
    def _get_next_item(self):
        data = next(self.cursor)
        assert data['_id']
        item = self.selector(data)
        assert item.id
        # log.debug('query found data %s',data)
        return item
        
    def __iter__(self):
        return self
       
    def __next__(self):
        while self.skipped < self.skip:
            self._skip()
        if self.taken == self.limit:
            raise StopIteration()
        return self._take()
    
    