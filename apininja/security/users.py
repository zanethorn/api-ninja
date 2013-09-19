from apininja.data import *

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
    
@known_type('users')
class Users(DataContainer):
    pass