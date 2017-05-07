#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Distrib script

Ussage:
python setup.py py2exe
"""

from distutils.core import setup

import py2exe

setup(
    name='IgcWeight',
    windows=[
        {
            'script': 'igcweight.py'
        }
    ],
    options={
        'py2exe': {
            'packages': 'sqlite3, decimal, mako',
            'includes': ['sqlalchemy.databases.sqlite'],
        }
    }
)
