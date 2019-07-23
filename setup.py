#!/usr/bin/env python

import sys

from wagtail import __version__
from wagtail.utils.setup import assets, sdist, check_bdist_egg

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


# Hack to prevent "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when setup.py exits
# (see http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing
except ImportError:
    pass


install_requires = [
    "Django>=2.0,<2.3",
    "django-modelcluster>=4.2,<5.0",
    "django-taggit>=0.23,<1.0",
    "django-treebeard>=4.2.0,<5.0",
    "djangorestframework>=3.7.4,<4.0",
    "draftjs_exporter>=2.1.5,<3.0",
    "Pillow>=4.0.0,<7.0.0",
    "beautifulsoup4>=4.5.1,<4.6.1",
    "html5lib>=0.999,<2",
    "Unidecode>=0.04.14,<2.0",
    "Willow>=1.1,<1.2",
    "requests>=2.11.1,<3.0",
    "pytz>=2016.6",  # for l18n
    "six>=1.11,<2.0",  # for l18n
]

# Testing dependencies
testing_extras = [
    # Required for running the tests
    'python-dateutil>=2.2',
    'pytz>=2014.7',
    'elasticsearch>=1.0.0,<3.0',
    'Jinja2>=2.8,<3.0',
    'boto3>=1.4,<1.5',
    'freezegun>=0.3.8',

    # For coverage and PEP8 linting
    'coverage>=3.7.0',
    'flake8>=3.6.0',
    'isort==4.2.5',
    'flake8-blind-except==0.1.1',
    'flake8-print==2.0.2',

    # For templates linting
    'jinjalint>=0.5',

    # Pipenv hack to fix broken dependency causing CircleCI failures
    'docutils==0.15',
]

# Documentation dependencies
documentation_extras = [
    'pyenchant==1.6.8',
    'sphinxcontrib-spelling>=2.3.0',
    'Sphinx>=1.5.2',
    'sphinx-autobuild>=0.6.0',
    'sphinx_rtd_theme>=0.1.9',
]

setup(
    name='wagtail',
    version=__version__,
    description='A Django content management system.',
    author='Wagtail core team + contributors',
    author_email='hello@wagtail.io',  # For support queries, please see http://docs.wagtail.io/en/stable/support.html
    url='http://wagtail.io/',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    long_description="Wagtail is an open source content management \
system built on Django, with a strong community and commercial support. \
It’s focused on user experience, and offers precise control for \
designers and developers.\n\n\
For more details, see https://wagtail.io, http://docs.wagtail.io and \
https://github.com/wagtail/wagtail/.",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Framework :: Django',
        'Framework :: Django :: 2.0',
        'Framework :: Django :: 2.1',
        'Framework :: Django :: 2.2',
        'Framework :: Wagtail',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=install_requires,
    extras_require={
        'testing': testing_extras,
        'docs': documentation_extras
    },
    entry_points="""
            [console_scripts]
            wagtail=wagtail.bin.wagtail:main
    """,
    zip_safe=False,
    cmdclass={
        'sdist': sdist,
        'bdist_egg': check_bdist_egg,
        'assets': assets,
    },
)
