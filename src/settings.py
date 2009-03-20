" Settings of igcweight "

from os import makedirs
from os.path import abspath, dirname, join, expanduser, isdir

try:
    from win32com.shell import shellcon, shell
    __homedir = shell.SHGetFolderPath(0, shellcon.CSIDL_APPDATA, 0, 0)
except ImportError:
    __homedir = expanduser("~")

HOME_DIR   = join(__homedir, '.igcweight')
PHOTOS_DIR = join(HOME_DIR, 'photos')
BASE_DIR   = abspath( join(dirname(__file__), '..') )

if not isdir(HOME_DIR):
    makedirs(HOME_DIR, mode=0755)
if not isdir(PHOTOS_DIR):
    makedirs(PHOTOS_DIR, mode=0755)


DEBUG = True

DB_ENGINE   = 'sqlite'
DB_HOST     = ''
DB_PORT     = ''
DB_DATABASE = join( HOME_DIR, 'igcweight.db' )
DB_USERNAME = ''
DB_PASSWORD = ''
DB_ARGS     = {}

VERSION = '0.3'
