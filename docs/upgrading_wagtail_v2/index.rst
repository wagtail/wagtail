==============================
Upgrading to Wagtail Version 2
==============================

Wagtail 2.0 Requirements
========================
* Django versions: 1.11, 2.0 
* Python versions: 3.4, 3.5, 3.6
    - It's recommended that you upgrade your python version first to be compatible with python 3.4.
    
For more requirements, see `Compatible Django / Python versions` table

Upgrade process
===============
We recommend upgrading one feature release at a time, even if your project is several versions behind the current one. This has a number of advantages over skipping directly to the newest release:

* If anything breaks as a result of the upgrade, you will know which version caused it, and will be able to troubleshoot accordingly;
* Deprecation warnings shown in the console output will notify you of any code changes you need to make before upgrading to the following version;
* Some releases make database schema changes that need to be reflected on your project by running ``./manage.py makemigrations`` - this is liable to fail if too many schema changes happen in one go.

Before upgrading to a new feature release:

* Check your project's console output for any deprecation warnings, and fix them where necessary;
* Check the new version's release notes, and the :ref:`Compatible Django / Python versions` table below, for any dependencies that need upgrading first;
* **IMPORTANT** Make a backup of your database. You may find yourself dropping and restoring your local database several times in order to get the django migrations to run correctly through the upgrades.

-----------
To upgrade
-----------
**Wagtail 2.0 Note** If you are upgrading to Wagtail 2.0, there is an update script for the module paths! See the :ref:`Wagtail 2.0 Module Path Update Script` section below for more information.

* Update the ``wagtail`` line in your project's ``requirements.txt`` file to specify the latest patch release of the version you wish to install. For example, to upgrade to version 1.8.x, the line should read::

    wagtail>=1.8,<1.9

* Run:

  .. code-block:: console

      pip install -r requirements.txt
      ./manage.py makemigrations
      ./manage.py migrate

* Make any necessary code changes as directed in the "Upgrade considerations" section of the release notes.
* Test that your project is working as expected.

Upgrading directly to Wagtail 2:
================================
During the deployment process, you may find that you want to try and upgrade directly to wagtail 2 without having to do multiple deployments. **WARNING:** You should first locally try to upgrade version by version to see if there are any major application issues before attempting to upgrade directly

* To experiment with upgrading directly instead of rolling out version by version, you can run all of the wagtail app migrations first.

-------------------------------------
Wagtail 2.0 Module Path Update Script
-------------------------------------
Many of the module paths within Wagtail have been reorganised to reduce duplication - for example, ``wagtail.wagtailcore.models`` is now ``wagtail.core.models``. As a result, ``import`` lines and other references to Wagtail modules will need to be updated when you upgrade to Wagtail 2.0. A new command has been added to assist with this - from the root of your project's code base:

   .. code-block:: console

       $ wagtail updatemodulepaths --list  # list the files to be changed without updating them
       $ wagtail updatemodulepaths --diff  # show the changes to be made, without updating files
       $ wagtail updatemodulepaths  # actually update the files

Or, to run from a different location:

   .. code-block:: console

       $ wagtail updatemodulepaths /path/to/project --list
       $ wagtail updatemodulepaths /path/to/project --diff
       $ wagtail updatemodulepaths /path/to/project

For the full list of command line options, enter ``wagtail help updatemodulepaths``.

You are advised to take a backup of your project codebase before running this command. The command will perform a search-and-replace over all \*.py files for the affected module paths; while this should catch the vast majority of module references, it will not be able to fix instances that do not use the dotted path directly, such as ``from wagtail import wagtailcore``.

The full list of modules to be renamed is as follows:

+-----------------------------------------+-----------------------------------+-----------------------------------+
| Old name                                | New name                          | Notes                             |
+=========================================+===================================+===================================+
| wagtail.wagtailcore                     | wagtail.core                      |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailadmin                    | wagtail.admin                     |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtaildocs                     | wagtail.documents                 | 'documents' no longer abbreviated |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailembeds                   | wagtail.embeds                    |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailimages                   | wagtail.images                    |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailsearch                   | wagtail.search                    |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailsites                    | wagtail.sites                     |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailsnippets                 | wagtail.snippets                  |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailusers                    | wagtail.users                     |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailforms                    | wagtail.contrib.forms             | Moved into 'contrib'              |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.wagtailredirects                | wagtail.contrib.redirects         | Moved into 'contrib'              |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailapi              | *removed*                         | API v1, removed in this release   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailfrontendcache    | wagtail.contrib.frontend_cache    | Underscore added                  |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailroutablepage     | wagtail.contrib.routable_page     | Underscore added                  |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailsearchpromotions | wagtail.contrib.search_promotions | Underscore added                  |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailsitemaps         | wagtail.contrib.sitemaps          |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+
| wagtail.contrib.wagtailstyleguide       | wagtail.contrib.styleguide        |                                   |
+-----------------------------------------+-----------------------------------+-----------------------------------+

Version numbers
===============

New feature releases of Wagtail are released approximately every two months. These releases provide new features, improvements and bugfixes, and are marked by incrementing the second part of the version number (for example, 1.11 to 1.12).

Additionally, patch releases will be issued as needed, to fix bugs and security issues. These are marked by incrementing the third part of the version number (for example, 1.12 to 1.12.1). Wherever possible, these releases will remain fully backwards compatible with the corresponding feature and not introduce any breaking changes.

A feature release will usually stop receiving patch release updates when the next feature release comes out. However, selected feature releases are designated as Long Term Support (LTS) releases, and will continue to receive maintenance updates to address any security and data-loss related issues that arise. Typically, a Long Term Support release will happen once every four feature releases and receive updates for five feature releases, giving a support period of ten months with a two months overlap.

Also, Long Term Support releases will ensure compatibility with at least one `Django Long Term Support release <https://www.djangoproject.com/download/#supported-versions>`_.

Exceptionally, with 2.0 introducing breaking changes, 1.13 was designated as LTS in addition to 1.12. The support period for both versions will last until the next LTS is released, some time around November 2018.

+-------------------+------------------------------------------+
| Wagtail release   | LTS support period                       |
+===================+==========================================+
| 0.8 LTS           | November 2014 - March 2016               |
+-------------------+------------------------------------------+
| 1.4 LTS           | March 2016 - December 2016               |
+-------------------+------------------------------------------+
| 1.8 LTS           | December 2016 - August 2017              |
+-------------------+------------------------------------------+
| 1.12 LTS          | August 2017 - November 2018 (expected)   |
+-------------------+------------------------------------------+
| 1.13 LTS          | October 2017 - November 2018 (expected)  |
+-------------------+------------------------------------------+

Deprecation policy
==================

Sometimes it is necessary for a feature release to deprecate features from previous releases. This will be noted in the "Upgrade considerations" section of the release notes.

When a feature is deprecated, it will continue to work in that feature release and the one after it, but will raise a warning. The feature will then be removed in the subsequent feature release. For example, a feature marked as deprecated in version 1.8 will continue to work in versions 1.8 and 1.9, and be dropped in version 1.10.

.. _compatible_django_python_versions:

Compatible Django / Python versions
===================================

New feature releases frequently add support for newer versions of Django and Python, and drop support for older ones. We recommend always carrying out upgrades to Django and Python as a separate step from upgrading Wagtail.

The compatible versions of Django and Python for each Wagtail release are:

+-------------------+------------------------------+-----------------------------+
| Wagtail release   | Compatible Django versions   | Compatible Python versions  |
+===================+==============================+=============================+
| 0.1               | 1.6                          | 2.7                         |
+-------------------+------------------------------+-----------------------------+
| 0.2               | 1.6                          | 2.7                         |
+-------------------+------------------------------+-----------------------------+
| 0.3               | 1.6                          | 2.6, 2.7                    |
+-------------------+------------------------------+-----------------------------+
| 0.4               | 1.6                          | 2.6, 2.7, 3.2, 3.3, 3.4     |
+-------------------+------------------------------+-----------------------------+
| 0.5               | 1.6                          | 2.6, 2.7, 3.2, 3.3, 3.4     |
+-------------------+------------------------------+-----------------------------+
| 0.6               | 1.6, 1.7                     | 2.6, 2.7, 3.2, 3.3, 3.4     |
+-------------------+------------------------------+-----------------------------+
| 0.7               | 1.6, 1.7                     | 2.6, 2.7, 3.2, 3.3, 3.4     |
+-------------------+------------------------------+-----------------------------+
| 0.8 LTS           | 1.6, 1.7                     | 2.6, 2.7, 3.2, 3.3, 3.4     |
+-------------------+------------------------------+-----------------------------+
| 1.0               | 1.7, 1.8                     | 2.7, 3.3, 3.4               |
+-------------------+------------------------------+-----------------------------+
| 1.1               | 1.7, 1.8                     | 2.7, 3.3, 3.4               |
+-------------------+------------------------------+-----------------------------+
| 1.2               | 1.7, 1.8                     | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.3               | 1.7, 1.8, 1.9                | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.4 LTS           | 1.8, 1.9                     | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.5               | 1.8, 1.9                     | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.6               | 1.8, 1.9, 1.10               | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.7               | 1.8, 1.9, 1.10               | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.8 LTS           | 1.8, 1.9, 1.10               | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.9               | 1.8, 1.9, 1.10               | 2.7, 3.3, 3.4, 3.5          |
+-------------------+------------------------------+-----------------------------+
| 1.10              | 1.8, 1.10, 1.11              | 2.7, 3.4, 3.5, 3.6          |
+-------------------+------------------------------+-----------------------------+
| 1.11              | 1.8, 1.10, 1.11              | 2.7, 3.4, 3.5, 3.6          |
+-------------------+------------------------------+-----------------------------+
| 1.12 LTS          | 1.8, 1.10, 1.11              | 2.7, 3.4, 3.5, 3.6          |
+-------------------+------------------------------+-----------------------------+
| 1.13 LTS          | 1.8, 1.10, 1.11              | 2.7, 3.4, 3.5, 3.6          |
+-------------------+------------------------------+-----------------------------+
| 2.0               | 1.11, 2.0                    | 3.4, 3.5, 3.6               |
+-------------------+------------------------------+-----------------------------+
| 2.1               | 1.11, 2.0                    | 3.4, 3.5, 3.6               |
+-------------------+------------------------------+-----------------------------+

