from apininja.data import *
from apininja.helpers import *
from datetime import *
import hashlib, re

def hash_password(password,salt):
    hasher = hashlib.sha512(bytes(salt,'utf-8'))
    hasher.update(bytes(password,'utf-8'))
    hashed = hasher.digest()
    return hashed

def generate_salt():
    return random_string(16)

@known_type('user')
class User(DataObject):
    email=attribute()
    name=attribute()
    password = attribute('password', server_only = True)
    last_login = attribute('last_login', server_only = True)
    last_activity = attribute('last_activity', server_only = True)
    failed_logins = attribute('failed_logins', default=0, server_only = True)
    last_failed_login = attribute('last_failed_login', server_only = True)
    locked = attribute('locked', server_only = True)
    salt = attribute('salt', server_only = True)
    owner_id = attribute('owner_id', server_only = True)
    roles = attribute('roles',default=[], server_only = True)
    tokens = attribute('tokens',default=[], server_only = True)
    
    def change_password(self,password):
        salt = generate_salt()
        hashed = hash_password(password,salt)
        self._data['salt'] = salt
        self._data['password'] = hashed
    
@known_type('token')
class AccessToken(DataObject):
    value = attribute('value')
    expires = attribute('expires')
    
@known_type('login')
class Login(DataObject):
    email = attribute('email')
    password = attribute('password')
    
@known_type('users')
class Users(DataContainer):
    item_type = 'user'
    
    def login(self,email,password):
        result = self.get(email)
        if result is None:
            print('user not found!')
            return None, None
        result = result._data
        salt = result['salt']
        hashed = result['password']
        now = datetime.utcnow()
        result['last_activity']= now
        result['last_updated'] = now
        new_hash = hash_password(password,salt)
        if  new_hash !=  hashed:
           result['failed_logins'] += 1
           result['last_failed_login'] = now
           if result['failed_logins'] >= int(config['RULES']['failed_logins']):
               result['locked'] = True
               result['tokens']=[]
           self._inner.save(result)
           return None,None

        salt = generate_salt()
        hashed = hash_password(password,salt)
        result['failed_logins'] =0
        result['last_login'] = now
        result['salt'] = salt
        result['password'] = hashed
        
        tokens = result['tokens'] 
        # for t in list(filter(lambda t: t['expires'] < now, tokens)):
            # tokens.remove(t)
        
        token_data = {
            'value':random_string(40),
            'created':now,
            'expires':now+timedelta(minutes=60)
            }
         
        tokens.append( token_data)
        result['tokens'] = tokens
        user = self.make_item(result)
        self.update(result)
        
        token = AccessToken(parent=user,data=token_data,context=self.context)
        return user, token
        
    def list(self,query={},limit=None,skip=0,select=None,**options):
        if 'search' in query:
            s = query['search']
            r = re.compile('^%s'%s,re.I)#{'$regex':'^%s'%s}
            query = { 
                '$or':  [
                        {'first_name':r},
                        {'last_name':r},
                        {'email':s}
                    ]
                }
        
        return super().list(query,limit,skip,select,**options)
        
    def get_user_by_token(self,token):
        return self.get({'tokens':{'$elemMatch':{'value':token}}})
    
    def get_id_query(self,id):
        if isinstance(id,dict):
            return id
        if id == 'me':
            if self.context.user:
                return {'_id':self.context.user.id}
        elif re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$',str(id),re.I):
            return {'email':id}
        return {'_id':id}