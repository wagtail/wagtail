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
    import multiprocessing  # noqa: F401
except ImportError:
    pass


install_requires = [
    "Django>=4.2,<6.0",
    "django-modelcluster>=6.2.1,<7.0",
    "django-permissionedforms>=0.1,<1.0",
    "django-taggit>=5.0,<5.1",
    "django-treebeard>=4.5.1,<5.0",
    "djangorestframework>=3.15.1,<4.0",
    "django-filter>=23.3,<25",
    "draftjs_exporter>=2.1.5,<6.0",
    "Pillow>=9.1.0,<11.0.0",
    "beautifulsoup4>=4.8,<4.13",
    "Willow[heif]>=1.8.0,<2",
    "requests>=2.11.1,<3.0",
    "l18n>=2018.5",
    "openpyxl>=3.0.10,<4.0",
    "anyascii>=0.1.5",
    "telepath>=0.3.1,<1",
    "laces>=0.1,<0.2",
]

# Testing dependencies
testing_extras = [
    # Required for running the tests
    "python-dateutil>=2.7",
    "pytz>=2014.7",
    "Jinja2>=3.0,<3.2",
    "boto3>=1.28,<2",
    "freezegun>=0.3.8",
    "azure-mgmt-cdn>=12.0,<13.0",
    "azure-mgmt-frontdoor>=1.0,<1.1",
    "django-pattern-library>=0.7",
    # For coverage and PEP8 linting
    "coverage>=3.7.0",
    "doc8==0.8.1",
    "ruff==0.1.5",
    # For enforcing string formatting mechanism in source files
    "semgrep==1.40.0",
    # For templates linting
    "curlylint==0.13.1",
    # For template indenting
    "djhtml==3.0.6",
    # For validating string formats in .po translation files
    "polib>=1.1,<2.0",
    # For wagtail.test.utils.wagtail_factories (used for streamfield migration toolkit)
    "factory-boy>=3.2",
    # For running tests in parallel
    "tblib>=2.0,<3.0",
]

# Documentation dependencies
documentation_extras = [
    "pyenchant>=3.1.1,<4",
    "sphinxcontrib-spelling>=7,<8",
    "Sphinx>=7.0",
    "sphinx-autobuild>=0.6.0",
    "sphinx-wagtail-theme==6.3.0",
    "myst_parser==2.0.0",
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
        "Changelog": "https://github.com/wagtail/wagtail/blob/main/CHANGELOG.txt",
        "Documentation": "https://docs.wagtail.org",
        "Source": "https://github.com/wagtail/wagtail",
        "Tracker": "https://github.com/wagtail/wagtail/issues",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Wagtail",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
    ],
    python_requires=">=3.8",
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
