" Settings of igcweight "

from os import mkdir
from os.path import abspath, dirname, join, expanduser, isdir
from decimal import Decimal

DEBUG = True

try:
    from win32com.shell import shellcon, shell
    USER_DIR = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
except ImportError:
    USER_DIR = expanduser("~")

LAST_OPEN_FILE_PATH = USER_DIR

HOME_DIR   = join( USER_DIR, 'igcweight-06' )
PHOTOS_DIR = join( HOME_DIR, 'photos' )
BASE_DIR   = abspath( join(dirname(__file__), '..') )
IMAGES_DIR = join( BASE_DIR, 'images' )

if not isdir(HOME_DIR):
    mkdir(HOME_DIR)
if not isdir(PHOTOS_DIR):
    mkdir(PHOTOS_DIR)

SHOW_PHOTO_APP = None

GEAR_HANDICAP = Decimal('0.02')
WINGLETS_HANDICAP = Decimal('0.01')
OWERWEIGHT_HANDICAP = Decimal('0.005')
OWERWEIGHT_STEP = 10

DB_ENGINE   = 'sqlite'
DB_HOST     = ''
DB_PORT     = ''
DB_DATABASE = join( HOME_DIR, 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

VERSION = '0.6'
