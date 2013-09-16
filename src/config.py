'''
Reads config.ini file and parses contents into local __dict__ for use by
other modules
'''

import configparser
import sys, os

__author__ = 'Zane Thorn'
__email__ = 'zthorn@shccs.com'
__copyright__='Copyright 2013, Signature Healthcare LLC.'
__license__ ='private'
__version__='1.0'

config =None
initialized = False

def init():
    '''
    Forces the config parser to reload the config file
    '''
    global config
    config = configparser.ConfigParser()
    config.read(os.getcwd()+'/config.ini')


#always load the dictionary the first time the file is run
if not initialized:
    init()
