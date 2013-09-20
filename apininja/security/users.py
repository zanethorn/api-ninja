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
    email=attribute('email')
    password = attribute('password')
    last_login = attribute('last_login')
    last_activity = attribute('last_activity')
    failed_logins = attribute('failed_logins', default=0)
    last_failed_login = attribute('last_failed_login')
    locked = attribute('locked')
    salt = attribute('salt')
    owner_id = attribute('owner_id')
    roles = attribute('roles',default=[])
    tokens = attribute('tokens',default=[])
    
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
           print('login failed')
           print(hashed)
           print(new_hash)
           result['failed_logins'] += 1
           result['last_failed_login'] = now
           if result['failed_logins'] >= int(config['RULES']['failed_logins']):
               result['locked'] = True
               result['tokens']=[]
           self._inner.save(result)
           return None,None

        salt = generate_salt()
        hashed = hash_password(password,salt)
        print('login success')
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
        
    def get_user_by_token(self,token):
        return self.get({'tokens':{'$elemMatch':{'value':token}}})
    
    def get_id_query(self,id):
        if id == 'me':
            return {'_id':self.context.user.id}
        elif re.match(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$',str(id),re.I):
            return {'email':id}
        return {'_id':id}