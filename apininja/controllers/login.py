from apininja.controllers import Controller
from apininja.log import log
from apininja.actions import *
from apininja.security.users import *
import os, time
import mimetypes
import email.utils

class LoginController(Controller):
    database = ''
    
    def __init__(self,app,context,config=None):
        super().__init__(app,context,config)
        if not self.database:
            self.database = self.context.endpoint.user_database
            
            
    def locate_resource(self,path):
        return Login()

    def get_allowed_actions(self,resource):
        return [GET,CREATE]
            
    def create(self, resource):
        db = self.app.get_database(self.database,self.context)
        users = db.get('users')
        data = self.request.data
        email = data['email']
        
        try:
            if self.request.options['reset']:
                return users.reset_password(email)
        except:
            pass
        
        password = data['password']
        
        user, token = users.login(email,password)
        assert user.id
        #log.debug('found user %s',user)
        data = {'user':user, 'token':token}
        
        return data
        
    def get(self, resource):
        return resource