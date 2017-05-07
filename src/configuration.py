"""
Read and write configuration
"""

from os.path import isfile
from decimal import Decimal
from ConfigParser import ConfigParser, DEFAULTSECT


class Configuration(object):
    """
    Parse config file
    """

    __defaults__ = {
        'gear_handicap': Decimal('0.02'),
        'winglets_handicap': Decimal('0.01'),
        'overweight_handicap': Decimal('0.005'),
        'overweight_step': 10,
        'allowed_difference': 2,
    }

    def __init__(self, fullpath, force_defaults=False):
        """
        __init__(self, str fullpath, bool force_defaults=False)
        """
        self.__fullpath = fullpath
        self.__force_defaults = force_defaults

        if not isfile(self.__fullpath):
            open(self.__fullpath, "w").close()

        self.read()
        self.save()

    def read(self):
        """
        read(self) - read configuration
        """
        defaults = {}
        for k in self.__defaults__.keys():
            defaults[k] = str(self.__defaults__[k])

        config = ConfigParser(defaults)

        if not self.__force_defaults:
            f = open(self.__fullpath, 'r')
            try:
                config.readfp(f)
            finally:
                f.close()

        self.set_gear_handicap(
            config.get(DEFAULTSECT, "gear_handicap"))
        self.set_winglets_handicap(
            config.get(DEFAULTSECT, "winglets_handicap"))
        self.set_overweight_handicap(
            config.get(DEFAULTSECT, "overweight_handicap"))
        self.set_overweight_step(
            config.get(DEFAULTSECT, "overweight_step"))
        self.set_allowed_difference(
            config.get(DEFAULTSECT, "allowed_difference"))

    def save(self):
        """
        save(self) - save configuration
        """
        config = ConfigParser()

        config.set(
            DEFAULTSECT, "gear_handicap", str(self.gear_handicap))
        config.set(
            DEFAULTSECT, "winglets_handicap", str(self.winglets_handicap))
        config.set(
            DEFAULTSECT, "overweight_handicap", str(self.overweight_handicap))
        config.set(
            DEFAULTSECT, "overweight_step", str(self.overweight_step))
        config.set(
            DEFAULTSECT, "allowed_difference", str(self.allowed_difference))

        f = open(self.__fullpath, 'wb')
        try:
            config.write(f)
        finally:
            f.close()

    @property
    def gear_handicap(self):
        return self.__gear_handicap

    def set_gear_handicap(self, value):
        self.__gear_handicap = Decimal(value)

    @property
    def winglets_handicap(self):
        return self.__winglets_handicap

    def set_winglets_handicap(self, value):
        self.__winglets_handicap = Decimal(value)

    @property
    def overweight_handicap(self):
        return self.__overweight_handicap

    def set_overweight_handicap(self, value):
        self.__overweight_handicap = Decimal(value)

    @property
    def overweight_step(self):
        return self.__overweight_step

    def set_overweight_step(self, value):
        self.__overweight_step = int(value)

    @property
    def allowed_difference(self):
        return self.__allowed_difference

    def set_allowed_difference(self, value):
        self.__allowed_difference = int(value)
