import re
from .helpers import *
from .log import log

arg_expression = re.compile(r'\{[\*]{0,2}[\w\d\_]+\}')

class RouteArgument():
    def __init__(self,name,is_arg=False,is_kwarg=False,default=None,spec=None):
        self.name = name
        self.is_arg = is_arg
        self.is_kwarg = is_kwarg
        self.default = default
        self.spec = spec
        
    

class Route(Configurable):
    name = ''
    protocols = ''
    controller = ''
    action =''
    path = ''
    
    def __init__(self,config = None):
        super().__init__(config)
        
        path = self.path
        arg_matches = arg_expression.findall(path)
        self.arguments = []
        
        path = '^'+path
        for a in arg_matches:  
            name = a[1:-1]
            #name, spec = name.split(':')
            spec = None
            is_arg = False
            is_kwarg = False
            default = None
            if name[:2] == '**':
                name = name[2:]
                is_kwarg = True
                path = path.replace(a,r'(?P<'+name+'>([\w\d]+(([.][\w\d]+)|([\/]))?)*)')
            elif name[:1] == '*':
                name = name[1:]
                is_arg = True
                path = path.replace(a,r'(?P<'+name+'>([\w\d]+(([.][\w\d]+)|([\/]))?)*)')
            else:
                path = path.replace(a,'(?P<'+name+'>[\w\d]+){1}')
               
            arg = RouteArgument(name,is_arg,is_kwarg,default,spec)
            self.arguments.append(arg)
        path+='$'

        self.expression = re.compile(path)
        
        arg_names = list(map(lambda a: a.name,self.arguments))
        if not self.controller and 'controller' not in arg_names:
            raise ValueError('Route (%s) does not map to a controller'%self.name)
        if not self.action and 'action' not in arg_names:
            self.action = 'index'
           
    def _handle_config_list(self,name,value):
        if name == 'protocols':
            self.protocols = value

    def is_match(self,request):
        if request.protocol in self.protocols:
            #log.debug('trying to match route %s to %s'%(self.expression.pattern,request.path))
            return bool(self.expression.match(request.full_path))
        return False

    def get_variables(self,path):
        args = {}
        matches = self.expression.search(path)
        variables = matches.groupdict()
        
        for arg in self.arguments:
            if arg.name not in variables:
                variables[arg.name] = arg.default
            if arg.is_arg:
                try:
                    variables[arg.name] = variables[arg.name].split('/')
                except:
                    pass
        if 'action' not in variables:
            variables['action'] = self.action
        return variables

