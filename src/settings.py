" Settings of igcweight "

from os import makedirs
from os.path import abspath, dirname, join, expanduser, isdir

DEBUG = True

try:
    from win32com.shell import shellcon, shell
    USER_DIR = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
except ImportError:
    USER_DIR = expanduser("~")

LAST_OPEN_FILE_PATH = USER_DIR

HOME_DIR   = join( USER_DIR, '.igcweight-05' )
PHOTOS_DIR = join( HOME_DIR, 'photos' )
BASE_DIR   = abspath( join(dirname(__file__), '..') )
IMAGES_DIR = join( BASE_DIR, 'images' )

if not isdir(HOME_DIR):
    makedirs(HOME_DIR, mode=0755)
if not isdir(PHOTOS_DIR):
    makedirs(PHOTOS_DIR, mode=0755)

SHOW_PHOTO_APP = None

DB_ENGINE   = 'sqlite'
DB_HOST     = ''
DB_PORT     = ''
DB_DATABASE = join( HOME_DIR, 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

VERSION = '0.5'
