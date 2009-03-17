" Database models "

import locale
import decimal

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, MetaData, Column
from sqlalchemy import Integer, SmallInteger, String, Text, Date, Numeric, CHAR, ForeignKey, Sequence
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, ForeignKeyConstraint
from sqlalchemy.orm import relation, backref


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
            return value
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        setattr( self, columnname, value )

    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -: str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        return self.GetDescription()


class Pilot(Base):
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
            return value
    
    def str_to_column(self, columnname, value):
        " str_to_column(self, str columnname, str value) - convert str value and store it in the columnt "
        if value == '':
            value = None
        elif columnname in ('age',):
            value = locale.atoi(value)
        setattr( self, columnname, value )
    
    @property
    def fullname(self):
        " fullname(self) -> str - get fullname Degree Firstname Surname "
        if self.degree != None:
            return "%s %s %s" % (self.degree, self.firstname, self.surname)
        else:
            return "%s %s" % (self.firstname, self.surname)

    def GetDescription(self, length=50):
        " GetDescription(self, int length=50) -: str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        return self.GetDescription()


class GliderType(Base):
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
        if columnname == 'coefficient':
            return locale.format("%.2f", value)
        else:
            return value
    
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
        " GetDescription(self, int length=50) -: str - get short description "
        return get_short_description(self.description, length)
    
    @property
    def short_description(self):
        return self.GetDescription()


#class Glider(Base):
#    __table__ = Table('glider', Base.metadata,
#        Column( 'glider_id', Integer, Sequence('glider_seq', optional=True), key='id', nullable=False ),
#        Column( 'registration', String(10), nullable=False ),
#        Column( 'competition_number', String(3), nullable=False ),
#        Column( 'glider_type_id', Integer, nullable=False ),
#        Column( 'description', Text ),
#        PrimaryKeyConstraint( 'id', name='pk_glider' ),
#        ForeignKeyConstraint( ('glider_type_id',), ('glider_type.id',), name='fk_glider_glider_type' ),
#        UniqueConstraint( 'registration', name='uq_glider_registration' ),
#        UniqueConstraint( 'competition_number', name='uq_glider_competition_number' )
#    )
#
#    glider_type = relation( GliderType, order_by=GliderType.name, backref='glider_type' )
#
#    def __init__(self, **kwargs):
#        """ Glider(self, str registration=None, str competition_number=None,
#        GliderType glider_type=None, str description=None) """
#        for key in kwargs.keys():
#            if hasattr(self, key):
#                setattr(self, key, kwargs[key])
#            else:
#                raise AttributeError( "'%s' object has no attribute '%s'" % (self.__class__.__name__, key) )
#        
#    def __repr__(self):
#        return "<Glider: #%s, '%s'>" % ( str(self.id), self.registration )
#    
#    def GetDescription(self, length=50):
#        " GetDescription(self, int length=50) -: str - get short description "
#        return __get_short_destcription(self.description, length)
#    
#    @property
#    def short_description(self):
#        return self.GetDescription()


from database import engine
Base.metadata.create_all(engine)
