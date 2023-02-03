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
    "Django>=3.2,<4.2",
    "django-modelcluster>=6.0,<7.0",
    "django-permissionedforms>=0.1,<1.0",
    "django-taggit>=2.0,<4.0",
    "django-treebeard>=4.5.1,<5.0",
    "djangorestframework>=3.11.1,<4.0",
    "django-filter>=2.2,<23",
    "draftjs_exporter>=2.1.5,<3.0",
    "Pillow>=4.0.0,<10.0.0",
    "beautifulsoup4>=4.8,<4.12",
    "html5lib>=0.999,<2",
    "Willow>=1.4,<1.5",
    "requests>=2.11.1,<3.0",
    "l18n>=2018.5",
    "openpyxl>=3.0.10,<4.0",
    "anyascii>=0.1.5",
    "telepath>=0.1.1,<1",
]

# Testing dependencies
testing_extras = [
    # Required for running the tests
    "python-dateutil>=2.7",
    "pytz>=2014.7",
    "elasticsearch>=5.0,<6.0",
    "Jinja2>=3.0,<3.2",
    "boto3>=1.16,<1.17",
    "freezegun>=0.3.8",
    "azure-mgmt-cdn>=12.0,<13.0",
    "azure-mgmt-frontdoor>=1.0,<1.1",
    "django-pattern-library>=0.7,<0.8",
    # For coverage and PEP8 linting
    "coverage>=3.7.0",
    "black==22.3.0",
    "flake8>=3.6.0",
    "isort==5.6.4",  # leave this pinned - it tends to change rules between patch releases
    "flake8-blind-except==0.1.1",
    "flake8-comprehensions==3.8.0",
    "flake8-print==5.0.0",
    "doc8==0.8.1",
    "flake8-assertive==2.0.0",
    # For enforcing string formatting mechanism in source files
    "semgrep==1.3.0",
    # For templates linting
    "curlylint==0.13.1",
    # For template indenting
    "djhtml==1.5.2",
    # for validating string formats in .po translation files
    "polib>=1.1,<2.0",
    # For streamfield migration toolkit
    "wagtail-factories @ git+https://github.com/gasman/wagtail-factories.git@remove-wagtail-upper-bound#egg=wagtail-factories",
]

# Documentation dependencies
documentation_extras = [
    "pyenchant>=3.1.1,<4",
    "sphinxcontrib-spelling>=5.4.0,<6",
    "Sphinx>=1.5.2",
    "sphinx-autobuild>=0.6.0",
    "sphinx-wagtail-theme==5.3.2",
    "myst_parser==0.18.1",
    "sphinx_copybutton>=0.5,<1.0",
]

setup(
    name="wagtail",
    version=__version__,
    description="A Django content management system.",
    author="Wagtail core team + contributors",
    author_email="hello@wagtail.org",  # For support queries, please see https://docs.wagtail.org/en/stable/support.html
    url="https://wagtail.org/",
    project_urls={
        "Documentation": "https://docs.wagtail.org",
        "Source": "https://github.com/wagtail/wagtail",
    },
    packages=find_packages(),
    include_package_data=True,
    license="BSD",
    long_description="Wagtail is an open source content management \
system built on Django, with a strong community and commercial support. \
It’s focused on user experience, and offers precise control for \
designers and developers.\n\n\
For more details, see https://wagtail.org, https://docs.wagtail.org and \
https://github.com/wagtail/wagtail/.",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Wagtail",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require={"testing": testing_extras, "docs": documentation_extras},
    entry_points="""
            [console_scripts]
            wagtail=wagtail.bin.wagtail:main
    """,
    zip_safe=False,
    cmdclass={
        "sdist": sdist,
        "bdist_egg": check_bdist_egg,
        "assets": assets,
    },
)
