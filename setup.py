#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='igcweight',
    version='0.9.7',
    description='IGC procedures for handicapped classes',
    author='Jan Seifert',
    author_email='jan.seifert@fotkyzcest.net',
    url='https://github.com/seifert/igcweight',
    license='BSD',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'mako',
        'sqlalchemy',
        'wx',
    ],
    entry_points={
        'console_scripts': [
            'igcweight = igcweight.main:main',
        ]
    },
)
