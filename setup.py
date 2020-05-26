#!/usr/bin/env/python
from setuptools import setup

setup(
    name='ckanext-initiatives',
    version='0.0.2',
    description='',
    license='GPL3',
    author='Grahame Bowland, QCIF',
    author_email='grahame.bowland@qcif.edu.au',
    url='https://github.com/BioplatformsAustralia/ckanext-initiatives/',
    namespace_packages=['ckanext'],
    packages=['ckanext.initiatives'],
    zip_safe=False,
    include_package_data=True,
    package_dir={'ckanext.initiatives': 'ckanext/initiatives'},
    package_data={'ckanext.initiatives': ['*.json', 'templates/*.html', 'templates/*/*.html', 'templates/*/*/*.html', 'static/*.css', 'static/*.png', 'static/*.jpg', 'static/*.css', 'static/*.ico']},
    entry_points="""
        [ckan.plugins]
        initiatives = ckanext.initiatives.plugins:BulkPlugin
    """
)
