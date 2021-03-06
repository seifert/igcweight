"""
Import and export data module
"""

import re
import codecs

from os.path import join, isdir
from os import mkdir
from shutil import copyfileobj, rmtree
from datetime import datetime
from tarfile import open as taropen
from xml.dom.minidom import getDOMImplementation, parse

from igcweight import settings

from igcweight.database import session
from igcweight.models import (
    GliderCard, Pilot, Organization, GliderType, Photo, DailyWeight)
from igcweight.configuration import Configuration

patternt_tar = re.compile(r'^.+\.tar$', re.IGNORECASE)
patternt_jpg = re.compile(r'^[a-z0-9]{32,32}\.jpg$', re.IGNORECASE)

MODELS = (Organization, Pilot, GliderType, GliderCard, Photo, DailyWeight)


def Export(fullpath):
    """
    Export(str fullpath) - export data into archive file
    """
    # Create XML
    impl = getDOMImplementation()
    xml = impl.createDocument(None, "igcweight", None)
    top_element = xml.documentElement
    # Add metadata into XML
    meta = xml.createElement('meta')
    element = xml.createElement('date')
    element.appendChild(
        xml.createTextNode(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    meta.appendChild(element)
    element = xml.createElement('version')
    element.appendChild(
        xml.createTextNode(".".join(str(s) for s in settings.VERSION_DB)))
    meta.appendChild(element)
    top_element.appendChild(meta)
    # Add preferences into XML
    preferences = xml.createElement('preferences')
    element = xml.createElement('gear_handicap')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.gear_handicap)))
    preferences.appendChild(element)
    element = xml.createElement('winglets_handicap')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.winglets_handicap)))
    preferences.appendChild(element)
    element = xml.createElement('overweight_handicap')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.overweight_handicap)))
    preferences.appendChild(element)
    element = xml.createElement('overweight_step')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.overweight_step)))
    preferences.appendChild(element)
    element = xml.createElement('underweight_handicap')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.underweight_handicap)))
    preferences.appendChild(element)
    element = xml.createElement('underweight_step')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.underweight_step)))
    preferences.appendChild(element)
    element = xml.createElement('allowed_difference')
    element.appendChild(
        xml.createTextNode(str(settings.configuration.allowed_difference)))
    preferences.appendChild(element)
    top_element.appendChild(preferences)
    # Add models data into XML
    for model in MODELS:
        model_name = model.__name__
        table_name = model.__table__.name
        element_table = xml.createElement('model')
        attribute = xml.createAttribute('name')
        element_table.setAttributeNode(attribute)
        element_table.setAttribute('name', table_name)
        attribute = xml.createAttribute('type')
        element_table.setAttributeNode(attribute)
        element_table.setAttribute('type', model_name)
        query = session.query(model).all()
        for row in query:
            element_row = xml.createElement(table_name)
            for column in model.__table__.columns:
                column_name = column.key
                element = xml.createElement(column_name)
                element.appendChild(
                    xml.createTextNode(row.column_as_str(column_name, False)))
                element_row.appendChild(element)
            element_table.appendChild(element_row)
        top_element.appendChild(element_table)
    # Save XML
    f = codecs.open(settings.XML_DATA, 'w', encoding='utf-8')
    try:
        xml.writexml(f, encoding='utf-8')
    finally:
        f.close()

    # Create TAR
    tar = taropen(fullpath, 'w')
    try:
        tar.add(settings.XML_DATA, 'igcweight.xml')
        query = session.query(Photo).all()
        for photo in query:
            tar.add(str(photo.full_path), str(photo.file_name))
    finally:
        tar.close()


def Import(fullpath, overwrite=False):
    """
    Import(str fullpath, overwrite=False) - import data from archive file
    """
    # Open TAR
    tar = taropen(fullpath, 'r')
    try:
        for file in tar.getnames():
            if file == 'igcweight.xml':
                # Import data
                src = tar.extractfile(file)
                try:
                    document = parse(src)
                    # Preferences
                    preferences = document.getElementsByTagName('preferences')
                    if len(preferences) == 1:
                        try:
                            for element in preferences[0].childNodes:
                                if element.nodeName == 'gear_handicap':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_gear_handicap(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'winglets_handicap':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_winglets_handicap(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'overweight_handicap':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_overweight_handicap(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'overweight_step':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_overweight_step(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'underweight_handicap':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_underweight_handicap(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'underweight_step':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_underweight_step(
                                            element.firstChild.nodeValue)
                                if element.nodeName == 'allowed_difference':
                                    if (element.firstChild and
                                            element.firstChild.nodeValue):
                                        settings.configuration.set_allowed_difference(
                                            element.firstChild.nodeValue)
                            settings.configuration.save()
                        except:
                            settings.configuration.read()
                            raise
                    # Data
                    for model in document.getElementsByTagName('model'):
                        model_name = model.attributes['type'].value
                        table_name = model.attributes['name'].value
                        model_obj = globals()[model_name]
                        for row in model.getElementsByTagName(table_name):
                            record = model_obj()
                            for attr in row.childNodes:
                                if (
                                        attr.firstChild and
                                        attr.firstChild.nodeValue):
                                    record.str_to_column(
                                        attr.nodeName,
                                        attr.firstChild.nodeValue,
                                        use_locale=False)
                            session.merge(record)
                            session.flush()
                    session.commit()
                finally:
                    src.close()
            if patternt_jpg.search(file):
                # Import photos
                dst = open(join(settings.PHOTOS_DIR, file), 'wb')
                try:
                    src = tar.extractfile(file)
                    try:
                        copyfileobj(src, dst)
                    finally:
                        src.close()
                finally:
                    dst.close()
    finally:
        tar.close()


def CleanDb(models, preferences, measured_weights):
    """
    CleanDb(list models, bool preferences, bool measured_weights) - clean
    db models, photos and settings
    """
    try:
        for model in models:
            session.query(model).delete()
            session.flush()

        if measured_weights:
            session.query(
                GliderCard
            ).update(
                {'glider_weight': None, 'pilot_weight': None,
                 'tow_bar_weight': None},
                synchronize_session=False)

        session.commit()
    except:
        session.rollback()
        raise

    if Photo in models:
        rmtree(settings.PHOTOS_DIR, ignore_errors=False)
        if not isdir(settings.PHOTOS_DIR):
            mkdir(settings.PHOTOS_DIR)
        rmtree(settings.IMG_CACHE_DIR, ignore_errors=False)
        if not isdir(settings.IMG_CACHE_DIR):
            mkdir(settings.IMG_CACHE_DIR)

    if preferences:
        Configuration(settings.CONFIG_FILE, force_defaults=True)
