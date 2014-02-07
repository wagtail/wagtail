#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='wagtail',
    version='0.1',
    description='A Django content management system focused on flexibility and user experience',
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='http://wagtail.io/',
    packages=['wagtail'],
    license='BSD',
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        "Django>=1.6.1",
        "South>=0.8.4",
        "django-compressor>=1.3",
        "django-celery>=3.1.1",
        "django-modelcluster>=0.1",
        "elasticutils>=0.8.2",
        "pyelasticsearch>=0.6.1",
        "Embedly>=0.5.0",
        "django-taggit==0.10",
        "Pillow>=2.3.0",
        "beautifulsoup4>=4.3.2",
        "lxml>=3.3.0",
        "BeautifulSoup==3.2.1",  # django-compressor gets confused if we have lxml but not BS3 installed
    ],
)
