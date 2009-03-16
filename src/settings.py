" Settings of igc-weight "

from os.path import join

from igcweight import BASE_DIR

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
DB_DATABASE = join( BASE_DIR, 'data', 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

VERSION = '0.2'
