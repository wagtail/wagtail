#!/usr/bin/env python

from wagtail import __version__
from wagtail.utils.setup import assets, check_bdist_egg, sdist


try:
    from setuptools import find_packages, setup
except ImportError:
    from distutils.core import setup


# Hack to prevent "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when setup.py exits
# (see http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing  # noqa
except ImportError:
    pass


install_requires = [
    "Django>=2.2,<3.3",
    "django-modelcluster>=5.1,<6.0",
    "django-taggit>=1.0,<2.0",
    "django-treebeard>=4.2.0,<5.0,!=4.5",
    "djangorestframework>=3.11.1,<4.0",
    "django-filter>=2.2,<3.0",
    "draftjs_exporter>=2.1.5,<3.0",
    "Pillow>=4.0.0,<9.0.0",
    "beautifulsoup4>=4.8,<4.10",
    "html5lib>=0.999,<2",
    "Willow>=1.4,<1.5",
    "requests>=2.11.1,<3.0",
    "l18n>=2018.5",
    "xlsxwriter>=1.2.8,<2.0",
    "tablib[xls,xlsx]>=0.14.0",
    "anyascii>=0.1.5",
    "telepath>=0.1.1,<1",
]

# Testing dependencies
testing_extras = [
    # Required for running the tests
    'python-dateutil>=2.2',
    'pytz>=2014.7',
    'elasticsearch>=5.0,<6.0',
    'Jinja2>=2.11,<3.0',
    'boto3>=1.16,<1.17',
    'freezegun>=0.3.8',
    'openpyxl>=2.6.4',
    'Unidecode>=0.04.14,<2.0',

    # For coverage and PEP8 linting
    'coverage>=3.7.0',
    'flake8>=3.6.0',
    'isort==5.6.4',  # leave this pinned - it tends to change rules between patch releases
    'flake8-blind-except==0.1.1',
    'flake8-print==2.0.2',
    'doc8==0.8.1',

    # For templates linting
    'jinjalint>=0.5',

    # Pipenv hack to fix broken dependency causing CircleCI failures
    'docutils==0.15',

    # django-taggit 1.3.0 made changes to verbose_name which affect migrations;
    # the test suite migrations correspond to >=1.3.0
    'django-taggit>=1.3.0,<2.0',
]

# Documentation dependencies
documentation_extras = [
    'pyenchant>=3.1.1,<4',
    'sphinxcontrib-spelling>=5.4.0,<6',
    'Sphinx>=1.5.2',
    'sphinx-autobuild>=0.6.0',
    'sphinx-wagtail-theme==5.0.4',
    'recommonmark>=0.7.1',
]

setup(
    name='wagtail',
    version=__version__,
    description='A Django content management system.',
    author='Wagtail core team + contributors',
    author_email='hello@wagtail.io',  # For support queries, please see https://docs.wagtail.io/en/stable/support.html
    url='https://wagtail.io/',
    packages=find_packages(),
    include_package_data=True,
    license='BSD',
    long_description="Wagtail is an open source content management \
system built on Django, with a strong community and commercial support. \
It’s focused on user experience, and offers precise control for \
designers and developers.\n\n\
For more details, see https://wagtail.io, https://docs.wagtail.io and \
https://github.com/wagtail/wagtail/.",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.0',
        'Framework :: Django :: 3.1',
        'Framework :: Django :: 3.2',
        'Framework :: Wagtail',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    python_requires='>=3.6',
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
