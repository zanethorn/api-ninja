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
    
    class MongodbAdapter(DataAdapter):
        system_container = '_system'
        key_type = bson.objectid.ObjectId
        
        def connect(self,connection):
            if isinstance(connection,str):
                connection = parse_connection(connection)
            server = connection['server']
            port = connection['port']
            db_name = connection['database']
            
            client = pymongo.MongoClient(server, int(port))
            db = client[db_name]
            return db
            
        def close_connection(self,connection):
            client = connection.connection
            client.close()
            
        def format_query(self, query, **options):
            for k,v in query.items():
                if isinstance(v,str):
                    try:
                        query[k] = ObjectId(v)
                    except:
                        pass
            return query

        def execute_command(self,command):
            db = command.database.db
            container_name = command.container.name
            container = db[container_name]
            
            if command.action == LIST:
                query  = self.format_query(command.query)
                cursor = container.find(query)
                return DataQuery(command.container,command.context,cursor,**command.options)
            else:
                method_name = action_map[command.action]
                method = getattr(container,method_name)
                if command.data:
                    data = command.data
                else:
                    data = self.format_query(command.query)
                log.debug('mongo executing %s(%s)',method_name,data)
                result = method(data)
                return result
            
except ImportError:
    pass
    
    