#!/usr/bin/env python

import sys


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


# Hack to prevent stupid TypeError: 'NoneType' object is not callable error on
# exit of python setup.py test # in multiprocessing/util.py _exit_function when
# running python setup.py test (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing
except ImportError:
    pass


PY3 = sys.version_info[0] == 3


install_requires = [
    "Django>=1.6.2,<1.7",
    "South>=0.8.4",
    "django-compressor>=1.3",
    "django-libsass>=0.1",
    "django-modelcluster>=0.1",
    "django-taggit==0.11.2",
    "django-treebeard==2.0",
    "Pillow>=2.3.0",
    "beautifulsoup4>=4.3.2",
    "lxml>=3.3.0",
    "Unidecode>=0.04.14",
    "six==1.7.3",
    'requests==2.3.0',
]


if not PY3:
    install_requires += [
        "unicodecsv>=0.9.4"
    ]


setup(
    name='wagtail',
    version='0.3.1',
    description='A Django content management system focused on flexibility and user experience',
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='http://wagtail.io/',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Framework :: Django',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=install_requires,
    zip_safe=False,
)
