" Read and write configuration "

from os.path import isfile
from decimal import Decimal
from ConfigParser import ConfigParser, DEFAULTSECT

class Configuration():
    " Parse config file "
    
    __defaults__ = {
                    'gear_handicap': '0.02',
                    'winglets_handicap': '0.01',
                    'overweight_handicap': '0.005',
                    'overweight_step': '10',
                    'allowed_difference': '2'
                   }
    
    def __init__(self, fullpath):
        " __init__(self, str fullpath) "
        self.__fullpath = fullpath
        
        if not isfile(self.__fullpath):
            open(self.__fullpath, "w").close()
        
        self.read()

    def read(self):
        " read(self) - read configuration "
        config = ConfigParser( self.__defaults__ )

        f = open(self.__fullpath, 'r')
        try:
            config.readfp(f)
        finally:
            f.close()
        
        self.GEAR_HANDICAP = Decimal( config.get(DEFAULTSECT, "gear_handicap") )
        self.WINGLETS_HANDICAP = Decimal( config.get(DEFAULTSECT, "winglets_handicap") )
        self.OVERWEIGHT_HANDICAP = Decimal( config.get(DEFAULTSECT, "overweight_handicap") )
        self.OVERWEIGHT_STEP = config.getint(DEFAULTSECT, "overweight_step")
        self.ALLOWED_DIFFERENCE = config.getint(DEFAULTSECT, "allowed_difference")
    
    def save(self):
        " save(self) - save configuration "
        config = ConfigParser()
        
        config.set( DEFAULTSECT, "gear_handicap", self.GEAR_HANDICAP )
        config.set( DEFAULTSECT, "winglets_handicap", self.WINGLETS_HANDICAP )
        config.set( DEFAULTSECT, "overweight_handicap", self.OVERWEIGHT_HANDICAP )
        config.set( DEFAULTSECT, "overweight_step", self.OVERWEIGHT_STEP )
        config.set( DEFAULTSECT, "allowed_difference", self.ALLOWED_DIFFERENCE )

        f = open(self.__fullpath, 'wb')
        try:
            config.write(f)
        finally:
            f.close()
