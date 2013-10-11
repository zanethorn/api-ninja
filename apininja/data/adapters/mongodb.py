from apininja.data import *
from apininja.data.query import *
from apininja.data.adapters import DataAdapter, parse_connection
from apininja.actions import *
from apininja.log import log

try:
    import pymongo, bson
    
    action_map = {
        LIST: 'find',
        GET:'find_one',
        CREATE:'insert',
        UPDATE:'save',
        DELETE:'remove'
        }
        
    simple_types.append(bson.objectid.ObjectId)
    DataObjectType.known_types['oid'] = bson.objectid.ObjectId
    
    db_clients = {}
    
    def get_client(server, port):
        addr = "%s:%s" % server + port
        if addr not in db_clients:
            db_clients[addr] = pymongo.MongoClient(server, int(port))
        return db_clients[addr]
    
    class MongodbAdapter(DataAdapter):
    
        def __init__(self,config=None):
            super().__init__(config)
            self.system_container = '_system'
            self.key_type = bson.objectid.ObjectId
        
        def connect(self,connection):
            if isinstance(connection,str):
                connection = parse_connection(connection)
            server = connection['server']
            port = connection['port']
            db_name = connection['database']
            
            client = get_client(server,port)
            db = client[db_name]
            return db
            
        def close_connection(self,connection):
            # client = connection.connection
            # client.close()
            
        def format_query(self, query, **options):
            output = {}
            for k,v in query.items():
                if isinstance(v,str):
                    try:
                        query[k] = self.parse_key(v)
                    except Exception as ex:
                        pass
            return query

        def execute_command(self,command):
            db = command.database.db
            container_name = command.container.name
            container = db[container_name]
            
            if command.action == LIST:
                query  = self.format_query(command.query)
                cursor = container.find(query)
                #log.debug('mongo running find(%s)',query)
                return DataQuery(command.container, command.context, cursor, **command.options)
                
            elif command.action == GET:
                query  = self.format_query(command.query)
                log.debug('mongo running %s.find_one(%s)',container.name,query)
                r = container.find_one(query)
                if not r:
                    return None
                assert r['_id']
                return r
                
            elif command.action == CREATE:
                data = command.data
                if '_id' in data:
                    del data['_id']
                id = container.insert(data, manipulate=True)
                if id:
                    data['_id'] = id
                #assert data['_id']
                return data
                
            elif command.action == UPDATE:
                query  = self.format_query(command.query)
                existing = container.find_one(query)
                data = command.data
                id = data['_id']
                del data['_id']
                update = {'$set': data}
                log.debug('mongo running find_and_modify(%s,%s)',query,update)
                r= container.find_and_modify(query=query,update=update, full_response=False,new=True)
                # try:
                    # log.debug('updated %s, %s', r, type(r))
                # except:
                    # pass
                # log.debug('server returned %s',r)
                if not r:
                    return None
                    
                try:
                    assert r['_id']
                except KeyError:
                    r['_id'] = id
                return r
                
            elif command.action == DELETE:
                query  = self.format_query(command.query)
                log.debug('mongo running remove(%s)',query)
                container.remove(query)
                return None
                
            else:
                raise ValueError(comamnd.action)
            
except ImportError:
    pass
    
    