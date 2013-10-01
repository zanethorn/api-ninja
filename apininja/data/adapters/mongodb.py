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
                log.debug('mongo running find(%s)',query)
                return DataQuery(command.container, command.context, cursor, **command.options)
            elif command.action == GET:
                query  = self.format_query(command.query)
                log.debug('mongo running find_one(%s)',query)
                return container.find_one(query)
            elif command.action == CREATE:
                data = command.data
                log.debug('mongo running insert(%s)',data)
                container.insert(data)
                return data
            elif command.action == UPDATE:
                query  = self.format_query(command.query)
                #existing = container.find_one(query)
                data = command.data
                del data['_id']
                update = {'$set': data}
                log.debug('mongo running find_and_modify(%s,%s)',query,update)
                r= container.find_and_modify(query,update)
                log.debug('returned %s',r)
            elif command.action == DELETE:
                query  = self.format_query(command.query)
                log.debug('mongo running remove(%s)',query)
                container.remove(query)
                return None
            else:
                raise ValueError(comamnd.action)
            
except ImportError:
    pass
    
    