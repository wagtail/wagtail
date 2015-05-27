#!/usr/bin/env python

import sys

from setuptools.command.sdist import sdist

from wagtail.wagtailcore import __version__
from wagtail.utils.setup import assets, add_subcommand, check_bdist_egg

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


PY3 = sys.version_info[0] == 3


install_requires = [
    "Django>=1.7.1,<1.9",
    "django-compressor>=1.4",
    "django-modelcluster>=0.6",
    "django-taggit>=0.13.0",
    "django-treebeard==3.0",
    "django-sendfile==0.3.7",
    "Pillow>=2.6.1",
    "beautifulsoup4>=4.3.2",
    "html5lib==0.999",
    "Unidecode>=0.04.14",
    "six>=1.7.0",
    'requests>=2.0.0',
    "Willow==0.2.1",
]


if not PY3:
    install_requires += [
        "unicodecsv>=0.9.4"
    ]


setup(
    name='wagtail',
    version=__version__,
    description='A Django content management system focused on flexibility and user experience',
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='http://wagtail.io/',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=install_requires,
    entry_points="""
            [console_scripts]
            wagtail=wagtail.bin.wagtail:main
    """,
    zip_safe=False,
    cmdclass={
        'sdist': add_subcommand(sdist, [('assets', None)]),
        'bdist_egg': check_bdist_egg,
        'assets': assets,
    },
)
