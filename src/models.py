" Database models "

import re
import locale
import decimal
import types

from os.path import join
from datetime import date, time, datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, MetaData, Column, ForeignKey, Sequence
from sqlalchemy import Integer, SmallInteger, String, Text, DateTime, Numeric, Boolean, CHAR
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy import desc
from sqlalchemy.orm import relation, backref
from sqlalchemy import types as sqltypes

import settings

pat = re.compile( locale.localeconv()['decimal_point'] )

def str_to_decimal(val):
    " str_to_decimal(str val) -> Decimal - convert string to Decimal "
    return decimal.Decimal( pat.sub('.', val) )

def get_short_description(description, length):
    " get_short_description(str description, int length) -> str - get short description "
    if description == None:
        return None
    l = len(description)
    if l <= 3:
        return description
    if length-3 <= 0:
        return '...'
    return l > length and '%s...' % description[0:length-3] or description

class Conversion():

    def column_as_str(self, columnname, use_locale=True):
        " column_as_str(self, str columnname, use_locale=False) -> str - return column value as string "
        column = getattr( self, columnname )
        column_type = type(column)

        if column_type == types.NoneType:
            # None
            value = ''
        elif column_type == types.IntType:
            # Int
            value = str(column)
        elif column_type == decimal.Decimal:
            # Decimal
            value = use_locale == True and locale.format("%.3f", column) or str(column)
        elif column_type == types.BooleanType:
            # Boolean
            value = column == True and "True" or "False"
        elif column_type == date:
            # date
            value = use_locale == True and column.strftime('%x') or column.strftime('%Y-%m-%d')
        elif column_type == time:
            # time
            value = use_locale == True and column.strftime('%X') or column.strftime('%H:%M:%S')
        elif column_type == datetime:
            # datetime
            value = use_locale == True and column.strftime('%x %X') or column.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Other datatypes
            value = unicode(column)
        
        return unicode(value)
    
    def str_to_column(self, columnname, value, use_locale=True):
        " str_to_column(self, str columnname, str value, use_locale=True) - convert str value and store it in the column "
        column = self.__table__.columns[columnname]
        column_type = column.type
        
        if value == '':
            # None
            value = None
        elif isinstance( column_type, (sqltypes.Integer, sqltypes.SmallInteger,) ):
            # Integer, SmallInteger
            value = int(value)
        elif isinstance( column_type, sqltypes.Numeric ):
            # Numeric
            value = use_locale == True and str_to_decimal(value) or decimal.Decimal(value)
        elif isinstance( column_type, sqltypes.Boolean ):
            # Boolean
            value = value == "True" and True or False
        elif isinstance( column_type, sqltypes.Date ):
            # Date
            value = use_locale == True and datetime.strptime( str(value), '%x' ) or datetime.strptime( str(value), '%Y-%m-%d' )
        elif isinstance( column_type, sqltypes.Time ):
            # Time
            value = use_locale == True and datetime.strptime( str(value), '%X' ) or datetime.strptime( str(value), '%H:%M:%S' )
        elif isinstance( column_type, sqltypes.DateTime ):
            # DateTime
            value = use_locale == True and datetime.strptime( str(value), '%x %X' ) or datetime.strptime( str(value), '%Y-%m-%d %H:%M:%S' )
        
        setattr( self, columnname, value )


Base = declarative_base()


class Organization(Base, Conversion):
    " Model Organization "
    
    __table__ = Table('organization', Base.metadata,
        Column( 'organization_id', Integer, Sequence('organization_seq', optional=True), key='id', nullable=False ),
        Column( 'name', String(50), nullable=False ),
        Column( 'code', String(4), nullable=False ),
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_organization' ),
        UniqueConstraint( 'name', name='uq_organization_name' ),
        UniqueConstraint( 'code', name='uq_organization_code' )
    )
    
    def __init__(self, **kwargs):
        " Organization(self, str name=None, str description=None "
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
    
    def __repr__(self):
        return "<Organization: #%s, '%s'>" % ( str(self.id), self.name )
    
    def __unicode__(self):
        return self.name

    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " Return short description, max. length is 50 chars "
        return self.GetDescription()


class Pilot(Base, Conversion):
    " Model Pilot "

    __table__ = Table('pilot', Base.metadata,
        Column( 'pilot_id', Integer, Sequence('pilot_seq', optional=True), key='id', nullable=False ),
        Column( 'degree', String(15) ),
        Column( 'firstname', String(24), nullable=False ),
        Column( 'surname', String(35), nullable=False ),
        Column( 'year_of_birth', SmallInteger ),
        Column( 'sex', CHAR(1) ),
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_pilot' ),
        UniqueConstraint( 'surname', 'firstname', 'degree', name='uq_pilot_name' )
    )
    
    def __init__(self, **kwargs):
        """ Pilot(self, str degree=None, str firstname=None, str surname=None,
        int year_of_birth=None, str sex=None, str description=None """
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
    
    def __repr__(self):
        return "<Pilot: #%s, '%s'>" % ( str(self.id), self.fullname )
    
    def __unicode__(self):
        return self.fullname
    
    @property
    def fullname(self):
        " fullname(self) -> str - get fullname Degree Firstname Surname "
        fullanme = "%s %s" % (self.firstname, self.surname)
        if self.degree != None:
            fullanme = "%s %s" % (self.degree, fullanme)
        return fullanme
    
    @property
    def fullname_rev(self):
        " fullname_rev(self) -> str - get fullname Surname Firstname Degree "
        fullanme = "%s %s" % (self.surname, self.firstname)
        if self.degree != None:
            fullanme = "%s %s" % (fullanme, self.degree)
        return fullanme

    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " Return short description, max. length is 50 chars "
        return self.GetDescription()


class GliderType(Base, Conversion):
    " Model GliderType "

    __table__ = Table('glider_type', Base.metadata,
        Column( 'glider_type_id', Integer, Sequence('glider_type_seq', optional=True), key='id', nullable=False ),
        Column( 'name', String(50), nullable=False ),
        Column( 'coefficient', Numeric(precision=3, scale=2), nullable=False ),
        Column( 'weight_non_lifting', SmallInteger ),
        Column( 'mtow_without_water', SmallInteger ),
        Column( 'mtow', SmallInteger ),
        Column( 'weight_referential', SmallInteger ),
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_glider_type' ),
        UniqueConstraint( 'name', name='uq_glider_type_name' )
    )
    
    def __init__(self, **kwargs):
        """ GliderType(self, str name=None, Decimal coefficient=None, int weight_non_lifting=None,
        int mtow_without_water=None, int mtow=None, int weight_referential=None, str description=None """
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
    
    def __repr__(self):
        return "<GliderType: #%s, '%s'>" % ( str(self.id), self.name )
    
    def __unicode__(self):
        return self.name
    
    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " Return short description, max. length is 50 chars "
        return self.GetDescription()


class Photo(Base, Conversion):
    " Model Photo "

    __table__ = Table('photo', Base.metadata,
        Column( 'photo_id', Integer, Sequence('photo_seq', optional=True), key='id', nullable=False ),
        Column( 'glider_card_id', Integer, nullable=False ),
        Column( 'md5', String(32), nullable=False ),
        Column( 'main', Boolean, nullable=False ),
        PrimaryKeyConstraint( 'id', name='pk_photo' ),
        UniqueConstraint( 'md5', name='uq_photo_md5' ),
        ForeignKeyConstraint( ('glider_card_id',), ('glider_card.id',), name='fk_photo_glider_card' )
    )
    
    def __init__(self, **kwargs):
        " Photo(self, GliderCard glider_card=None, bool main=None, str description=None) "
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
        
    def __repr__(self):
        return "<Photo: #%s %s>" % ( str(self.id), self.md5 )
    
    def __unicode__(self):
        return "%s - %s" % ( str(self.id), self.glider_card )
    
    @property
    def file_name(self):
        " Returns photo file name "
        return "%s.jpg" % self.md5
    
    @property
    def full_path(self):
        " Returns photo full path "
        return join( settings.PHOTOS_DIR, self.file_name )


class DailyWeight(Base, Conversion):
    " Model DailyWeight "

    __table__ = Table('daily_weight', Base.metadata,
        Column( 'daily_weight_id', Integer, Sequence('daily_weight_seq', optional=True), key='id', nullable=False ),
        Column( 'glider_card_id', Integer, nullable=False ),
        Column( 'date', DateTime, nullable=False ),
        Column( 'tow_bar_weight', SmallInteger, nullable=False ),
        PrimaryKeyConstraint( 'id', name='pk_daily_weight' ),
        UniqueConstraint( 'glider_card_id', 'date', name='uq_daily_weight_date' ),
        ForeignKeyConstraint( ('glider_card_id',), ('glider_card.id',), name='fk_daily_weight_glider_card' )
    )
    
    def __init__(self, **kwargs):
        " GliderCard(self, GliderCard glider_card=None, date date=None, int weight=None) "
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
        
    def __repr__(self):
        return "<DailyWeight: #%s %s %d>" % ( str(self.id), self.date, self.tow_bar_weight )
    
    def __unicode__(self):
        return "%s, %s" % ( self.glider_card, self.date )

    @property
    def tow_bar_difference(self):
        " tow_bar_difference -> int or None - return difference between glider card and current tow bar weights "
        if self.tow_bar_weight != None and self.glider_card.tow_bar_weight != None:
            return self.tow_bar_weight - self.glider_card.tow_bar_weight
        else:
            return None


class GliderCard(Base, Conversion):
    " Model GliderCard "

    __table__ = Table('glider_card', Base.metadata,
        Column( 'glider_card_id', Integer, Sequence('glider_card_seq', optional=True), key='id', nullable=False ),
        Column( 'registration', String(10), nullable=False ),
        Column( 'competition_number', String(5), nullable=False ),
        Column( 'glider_type_id', Integer, nullable=False ),
        Column( 'pilot_id', Integer, nullable=False ),
        Column( 'organization_id', Integer, nullable=False ),
        Column( 'landing_gear', Boolean, nullable=False ),
        Column( 'winglets', Boolean, nullable=False ),
        Column( 'certified_weight_non_lifting', SmallInteger ),
        Column( 'certified_empty_weight', SmallInteger ),
        Column( 'certified_min_seat_weight', SmallInteger ),
        Column( 'certified_max_seat_weight', SmallInteger ),
        Column( 'glider_weight', SmallInteger ),
        Column( 'pilot_weight', SmallInteger ),
        Column( 'tow_bar_weight', SmallInteger ),
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_glider_card' ),
        ForeignKeyConstraint( ('glider_type_id',), ('glider_type.id',), name='fk_glider_card_glider_type' ),
        ForeignKeyConstraint( ('pilot_id',), ('pilot.id',), name='fk_glider_card_pilot' ),
        ForeignKeyConstraint( ('organization_id',), ('organization.id',), name='fk_glider_card_organization' ),
        UniqueConstraint( 'registration', name='uq_glider_card_registration' ),
        UniqueConstraint( 'competition_number', name='uq_glider_card_competition_number' ),
        UniqueConstraint( 'pilot_id', name='uq_glider_card_pilot' )
    )

    glider_type = relation( GliderType, order_by=GliderType.name )
    pilot = relation( Pilot, order_by=Pilot.surname )
    organization = relation( Organization, order_by=Organization.name )
    photos = relation( Photo, order_by=Photo.id, backref='glider_card', cascade='all' )
    daily_weight = relation(DailyWeight, order_by=desc(DailyWeight.date), backref='glider_card', cascade='all' )

    def __init__(self, **kwargs):
        """ GliderCard(self, str registration=None, str competition_number=None, GliderType glider_type=None,
        Pilot pilot=None, Organization organization=None, str description=None) """
        for key in kwargs.keys():
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
        
    def __repr__(self):
        return "<GliderCard: #%s, '%s', '%s'>" % ( str(self.id), self.registration, self.competition_number )
    
    def __unicode__(self):
        return "%s, %s" % ( self.registration, self.competition_number )
    
    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " short_description -> str - return short description, max. length is 50 chars "
        return self.GetDescription()

    @property
    def main_photo(self):
        " main_photo -> Photo - return main photo or None "
        if len(self.photos) > 0:
            for p in self.photos:
                if p.main == True: 
                    return p
        return None
    
    @property
    def referential_weight(self):
        " referential_weight -> int or None - return competition referential weight "
        if self.glider_weight != None and self.pilot_weight != None:
            return self.glider_weight + self.pilot_weight
        else:
            return None
    
    @property
    def referential_difference(self):
        " referential_difference -> int or None - return difference between measured and igc weight "
        if self.referential_weight != None and self.glider_type.weight_referential != None:
            return self.referential_weight - self.glider_type.weight_referential
        else:
            return None
    
    @property
    def coefficient(self):
        " coefficient -> int or None - return competition coefficient "
        referential_difference = self.referential_difference
        if referential_difference != None:
            gear_handicap = self.landing_gear and settings.configuration.gear_handicap or 0
            winglets_handicap = self.winglets and settings.configuration.winglets_handicap or 0
            coefficient = self.glider_type.coefficient + gear_handicap + winglets_handicap
            if referential_difference > 0:
                overweight_handicap = referential_difference / settings.configuration.overweight_step
                if overweight_handicap * settings.configuration.overweight_step < referential_difference:
                    overweight_handicap = overweight_handicap + 1
                overweight_handicap = overweight_handicap * settings.configuration.overweight_handicap
                coefficient = coefficient + overweight_handicap
            return coefficient
        else:
            return None
    
    @property
    def non_lifting_difference(self):
        " non_lifting_difference -> int or None - return difference between certified and igc non-lifting parts weight "
        if self.certified_weight_non_lifting != None and self.glider_type.weight_non_lifting != None:
            return self.certified_weight_non_lifting - self.glider_type.weight_non_lifting
        else:
            return None
    
    @property
    def mtow_difference(self):
        " mtow_difference -> int or None - return difference between measured and igc mtow "
        if self.glider_type.mtow_without_water != None:
            mtow = self.glider_type.mtow_without_water
        else:
            if self.glider_type.mtow != None:
                mtow = self.glider_type.mtow
            else:
                mtow = None
        referential_weight = self.referential_weight
        if referential_weight != None and mtow != None:
            return referential_weight - self.glider_type.mtow
        else:
            return None
    
    @property
    def seat_weight_difference(self):
        " seat_weight_difference -> int or None - return difference between certified and igc non-lifting parts weight  "
        if self.certified_min_seat_weight != None and self.certified_max_seat_weight != None and self.pilot_weight != None:
            if self.pilot_weight < self.certified_min_seat_weight:
                return self.pilot_weight - self.certified_min_seat_weight
            elif self.pilot_weight > self.certified_max_seat_weight:
                return self.pilot_weight - self.certified_max_seat_weight
            else:
                return 0
        else:
            return None


from database import engine
Base.metadata.create_all(engine)
