" Database connection and sessions "

from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings

__engine_url = { 'drivername': settings.DB_ENGINE, 'query': settings.DB_ARGS }
if settings.DB_USERNAME != '': __engine_url['username'] = settings.DB_USERNAME
if settings.DB_PASSWORD != '': __engine_url['password'] = settings.DB_PASSWORD
if settings.DB_HOST != '': __engine_url['host'] = settings.DB_HOST
if settings.DB_PORT != '': __engine_url['port'] = settings.DB_PORT
if settings.DB_DATABASE != '': __engine_url['database'] = settings.DB_DATABASE

engine = create_engine( URL(**__engine_url), echo=settings.DEBUG, convert_unicode=True )

Session = sessionmaker(bind=engine, autoflush=True, transactional=True)
session = Session()
