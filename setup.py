from distutils.core import setup

setup(
    name='apininja',
    version='0.1dev',
    author='Zane Thorn',
    author_email='zthorn@shccs.com',
    packages=[
        'apininja',
        'apininja.endpoints',
        'apininja.controllers',
        'apininja.data',
        'apininja.data.adapters',
        'apininja.data.formatters',
        'apininja.expressions',
        'apininja.security'
        ],
    license=open('LICENSE').read(),
    description='An API-focused content-management platform',
    long_description=open('README.md').read(),
)
