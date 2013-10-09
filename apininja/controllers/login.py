from apininja.controllers import Controller
from apininja.log import log
from apininja.actions import *
from apininja.security import *
import os, time, datetime
import mimetypes
import email.utils

class LoginController(Controller):
    database = ''
    
    def __init__(self,app,context,config=None):
        super().__init__(app,context,config)
        if not self.database:
            self.database = self.context.endpoint.user_database
            
            
    def locate_resource(self,path):
        l = find_type('login')
        return l(context=self.context)

    def get_allowed_actions(self,resource):
        return [GET, CREATE, DELETE]
        
    def can_access_resource(self,resource):
        return True
            
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
        
        self.context.user = root
        
        user, token = users.login(email,password)
        if not user:
            self.response.send_error(self.context.endpoint.STATUS_UNAUTHORIZED,'Invalid Email address or Password')
        assert user.id
        data = {'user':user, 'token':token}
        
        return data
        
    def get(self, resource):
        return resource
        
    def delete(self, resource):
        if not self.context.user:
            self.response.unauthorized()
    
        db = self.app.get_database(self.database,self.context)
        users = db.get('users')
        
        user = self.context.user
        token = self.request.variables['token']
        for ix,t in enumerate(user.tokens):
            if token == t.id:
                del user.tokens[ix]
        users.update(user)
        
        self.response.variables['token'] = ' ;expires=' + str( datetime.datetime.now() )
        return None