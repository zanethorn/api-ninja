import os.path


my_path = os.path.dirname(__file__)
mods = []
for module in os.listdir(my_path):
    if module =='__init__.py' or module[-3:] != '.py' :
        continue
    mods.append(module[:-3])
__all__=mods
