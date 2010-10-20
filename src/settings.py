" Settings of igcweight "

from os import mkdir
from os.path import abspath, dirname, join, expanduser, isdir, isfile
from sys import argv
from getopt import getopt

from configuration import Configuration

VERSION_APP = (0, 9, 4)
VERSION_DB  = (0, 9)
VERSION = ".".join( str(s) for s in VERSION_APP )

DEBUG = True

HOME_DIR = None
__optlist, __args = getopt( argv[1:], 'd:' )
for __o, __v in __optlist:
    if __o == '-d':
        HOME_DIR = abspath(__v)
        break

try:
    from win32com.shell import shellcon, shell
    USER_DIR = shell.SHGetFolderPath( 0, shellcon.CSIDL_APPDATA, 0, 0 )
except ImportError:
    USER_DIR = expanduser("~")

LAST_OPEN_FILE_PATH = USER_DIR

#HOME_DIR       = HOME_DIR == None and join( USER_DIR, '.igcweight' ) or HOME_DIR
HOME_DIR       = HOME_DIR == None and join( USER_DIR, 'igcweight-%s' % "".join( str(s) for s in VERSION_DB ) ) or HOME_DIR
PHOTOS_DIR     = join( HOME_DIR, 'photos' )
IMG_CACHE_DIR  = join( HOME_DIR, 'thumbnails' )
BASE_DIR       = abspath( join(dirname(__file__), '..') )
IMAGES_DIR     = join( BASE_DIR, 'images' )
LOCALE_DIR     = join( BASE_DIR, 'locale' )
TEMPLATES_DIR  = join( BASE_DIR, 'templates' )
CONFIG_FILE    = join( HOME_DIR, 'igcweight.conf' )
XML_DATA       = join( HOME_DIR, 'igcweight.xml' )

if not isdir(HOME_DIR):
    mkdir(HOME_DIR)
if not isdir(PHOTOS_DIR):
    mkdir(PHOTOS_DIR)
if not isdir(IMG_CACHE_DIR):
    mkdir(IMG_CACHE_DIR)

SHOW_PHOTO_APP = None

DB_ENGINE   = 'sqlite'
DB_HOST     = ''
DB_PORT     = ''
DB_DATABASE = join( HOME_DIR, 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

configuration = Configuration( CONFIG_FILE )
