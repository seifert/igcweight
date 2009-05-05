" Import and export data module "

from tarfile import open

from database import session
from models import GliderCard, Pilot, Organization, GliderType, Photo , DailyWeight

def Export(filename):
    " Export(str filename) - export data into archive file "
    print filename
