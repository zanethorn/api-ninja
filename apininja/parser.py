import shlex

class CommandParser():
    def __init__(self,app):
        self.app = app
        
        
    def process_command(self,input):
        try:
            cmd, args = input.split(maxsplit=1)
            args = args.split()
        except ValueError:
            cmd = input
            args = []
        
        try:
            action = getattr(self,cmd)
        except AttributeError:
            return 'Command %s was not found' % cmd
            #try:
        r= action(*args)
        if not r:
            return ''
        if not isinstance(r,str):
            return '\r\n'.join(r)
        return r
            #except Exception as ex:
            #    return 'Command encountered exception %s'%str(ex)
        
        
    def exit(self,*args):
        self.app.shutdown()
        return 'Shutting down...'
        
    def restart(self,*args):
        self.app.restart()
        return 'Restarting system...'
        
    def list(self,*args):
        for a in args:
            a = a.lower()
            
            if a == 'controllers':
                yield 'Controllers:'
                for k in self.app.controllers.keys():
                    yield '\t%s' % k
            elif a == 'routes':
                yield 'Controllers:'
                for k in self.app.controllers.keys():
                    yield '\t%s' % k
            elif a == 'adapters':
                yield 'Controllers:'
                for k in self.app.controllers.keys():
                    yield '\t%s' % k
            elif a == 'database':
                yield 'Controllers:'
                for k in self.app.controllers.keys():
                    yield '\t%s' % k
            elif a ==  'endpoints':
                yield 'Controllers:'
                for k in self.app.controllers.keys():
                    yield '\t%s' % k
            else:
                raise ValueError('Unrecognized provider %s'%a)