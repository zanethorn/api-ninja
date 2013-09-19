import apininja.app

class App(apininja.app.ApiApplication):
    def __init__(self):
        super().__init__()

app = App()

if __name__ == '__main__':
    app.run()
##    db = app.get_database('shccs')
##    users = db.get('users')
##    print(users)
##    system = db.db['_system']
##    users = system.find_one({'name':'users'})
##    print(users)
##    all = system.find({})
##    for a in all:
##        print(a)
