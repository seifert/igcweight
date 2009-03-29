" Database models "

import locale
import decimal

from os.path import join
from datetime import date

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, MetaData, Column
from sqlalchemy import Integer, SmallInteger, String, Text, Date, Numeric, Boolean, CHAR, ForeignKey, Sequence
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relation, backref

from settings import PHOTOS_DIR

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


Base = declarative_base()


class Organization(Base):
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

    def column_as_str(self, columnname):
        " column_as_str(self, str columnname) -> str - return column value as string "
        value = getattr( self, columnname )
        
        if value == None:
            return ''
        else:
            return unicode(value)
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        setattr( self, columnname, value )

    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " Return short description, max. length is 50 chars "
        return self.GetDescription()


class Pilot(Base):
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

    def column_as_str(self, columnname):
        " column_as_str(self, str columnname) -> str - return column value as string "
        value = getattr( self, columnname )
        
        if value == None:
            return ''
        elif columnname in ('year_of_birth',):
            return locale.format("%d", value)
        else:
            return unicode(value)
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        elif columnname in ('year_of_birth',):
            value = locale.atoi(value)
        setattr( self, columnname, value )
    
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


class GliderType(Base):
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

    def column_as_str(self, columnname):
        " column_as_str(self, str columnname) -> str - return column value as string "
        value = getattr( self, columnname )
        
        if value == None:
            return ''
        elif columnname in ('weight_non_lifting', 'mtow_without_water', 'mtow', 'weight_referential'):
            return locale.format("%d", value)
        elif columnname == 'coefficient':
            return locale.format("%.2f", value)
        else:
            return unicode(value)
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        elif columnname in ('weight_non_lifting', 'mtow_without_water', 'mtow', 'weight_referential'):
            value = locale.atoi(value)
        elif columnname == 'coefficient':
            # TODO: improve???
            value = decimal.Decimal( str(locale.atof( value.encode('ascii') )) )
        setattr( self, columnname, value )
    
    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        " Return short description, max. length is 50 chars "
        return self.GetDescription()


class Photo(Base):
    " Model Photo "

    __table__ = Table('photo', Base.metadata,
        Column( 'photo_id', Integer, Sequence('photo_seq', optional=True), key='id', nullable=False ),
        Column( 'glider_card_id', Integer, nullable=False ),
        Column( 'main', Boolean, nullable=False ),
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_photo' ),
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
        return "<Photo: #%s %s>" % ( str(self.id), self.full_path )
    
    def __unicode__(self):
        return "%d - %s" % ( str(self.id), self.glider_card )

    def column_as_str(self, columnname):
        " column_as_str(self, str columnname) -> str - return column value as string "
        value = getattr( self, columnname )
        
        if value == None:
            return ''
        elif columnname == 'main':
            return value == True and _("True") or _("False")
        else:
            return unicode(value)
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        setattr( self, columnname, value )
    
    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return __get_short_destcription(self.description, length)
    
    @property
    def short_description(self):
        " Return shorts description, max. length is 50 chars "
        return self.GetDescription()
    
    @property
    def full_path(self):
        " Returns photo full path "
        return join( PHOTOS_DIR, "%08d.jpg" % self.id )


class GliderCard(Base):
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
        Column( 'description', Text ),
        PrimaryKeyConstraint( 'id', name='pk_glider_card' ),
        ForeignKeyConstraint( ('glider_type_id',), ('glider_type.id',), name='fk_glider_card_glider_type' ),
        ForeignKeyConstraint( ('pilot_id',), ('pilot.id',), name='fk_glider_card_pilot' ),
        ForeignKeyConstraint( ('organization_id',), ('organization.id',), name='fk_glider_card_organization' ),
        UniqueConstraint( 'registration', name='uq_glider_card_registration' ),
        UniqueConstraint( 'competition_number', name='uq_glider_card_competition_number' ),
        UniqueConstraint( 'pilot_id', name='uq_glider_card_pilot' )
    )

    glider_type = relation( GliderType, order_by=GliderType.name, backref='glider_type' )
    pilot = relation( Pilot, order_by=Pilot.surname, backref='pilot' )
    organization = relation( Organization, order_by=Organization.name, backref='organization' )
    photos = relation(Photo, backref=backref('photo', order_by='id'), cascade="all, delete, delete-orphan")

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

    def column_as_str(self, columnname):
        " column_as_str(self, str columnname) -> str - return column value as string "
        value = getattr( self, columnname )
        
        if value == None:
            return ''
        elif columnname in ('landing_gear', 'winglets'):
            return value == True and _("True") or _("False")
        else:
            return unicode(value)
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        setattr( self, columnname, value )
    
    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -> str - get short description "
        return __get_short_destcription(self.description, length)
    
    @property
    def short_description(self):
        " short_description -> str - return short description, max. length is 50 chars "
        return self.GetDescription()

    @property
    def main_photo(self):
        " main_photo -> Photo - return main photo "
        for photo in self.photos:
            if photo.main == True:
                return photo
        return None


from database import engine
Base.metadata.create_all(engine)
