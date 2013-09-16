from distutils.core import setup

setup(
    name='api-ninja',
    version='0.1dev',
    author='Zane Thorn',
    author_email='zthorn@shccs.com',
    packages=['src','src.endpoints','src.controllers'],
    license=open('LICENSE').read(),
    description='An API-focused content-management platform',
    long_description=open('README').read(),
)
