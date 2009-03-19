" Settings of igc-weight "

from os.path import abspath, dirname, join

BASE_DIR   = abspath( join(dirname(__file__), '..') )
DATA_DIR   = join(BASE_DIR, 'data')
PHOTOS_DIR = join(DATA_DIR, 'photos')

DEBUG = True

#DB_ENGINE   = 'firebird'
#DB_HOST     = 'localhost'
#DB_PORT     = ''
#DB_DATABASE = 'igcweight'
#DB_USERNAME = 'IGCWEIGH'
#DB_PASSWORD = 'igc'
#DB_ARGS     = {}

DB_ENGINE   = 'sqlite'
DB_HOST     = ''
DB_PORT     = ''
DB_DATABASE = join( DATA_DIR, 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

VERSION = '0.3'
