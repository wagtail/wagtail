#!/usr/bin/env python

import os
from setuptools import setup
from setuptools.command.test import test


def root_dir():
    rd = os.path.dirname(__file__)
    if rd:
        return rd
    return '.'


class pytest_test(test):
    def finalize_options(self):
        test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        pytest.main([])


setup_args = dict(
    name='django-treebeard',
    version='2.0b2',
    url='https://tabo.pe/projects/django-treebeard/',
    author='Gustavo Picon',
    author_email='tabo@tabo.pe',
    license='Apache License 2.0',
    packages=['treebeard', 'treebeard.templatetags', 'treebeard.tests'],
    package_dir={'treebeard': 'treebeard'},
    package_data={
        'treebeard': ['templates/admin/*.html', 'static/treebeard/*']},
    description='Efficient tree implementations for Django 1.4+',
    long_description=open(root_dir() + '/README.rst').read(),
    cmdclass={'test': pytest_test},
    install_requires=['Django>=1.4'],
    tests_require=['pytest'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'])


if __name__ == '__main__':
    setup(**setup_args)
