from distutils.core import setup
import os

packages = [
        'apininja',
        'apininja.endpoints',
        'apininja.controllers',
        'apininja.data',
        'apininja.data.adapters',
        'apininja.data.formatters',
        'apininja.expressions',
        'apininja.security',
        'apininja.plugins'
        ]

path = './apininja/plugins'
for p in os.listdir(path):
    if os.path.isdir(os.path.join(path,p)):
        pck = 'apininja.plugins.%s'%p
        packages.append(pck)
        print('Adding plugin %s'%pck)

data_files = [
    ('apininja/data/formatters',['apininja/data/formatters/template.html'])
    ]

setup(
    name='apininja',
    version='0.1dev',
    author='Zane Thorn',
    author_email='zthorn@gmail.com',
    packages=packages,
    data_files = data_files,
    license=open('LICENSE').read(),
    description='An API-focused content-management platform',
    long_description=open('README.md').read(),
)
