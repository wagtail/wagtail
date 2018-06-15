==============================
Upgrading to Wagtail Version 2
==============================

Wagtail 2.0 Requirements
========================
* Django versions: 1.11, 2.0 
* Python versions: 3.4, 3.5, 3.6
    - It's recommended that you upgrade your python version first to be compatible with python 3.4.
    
For more requirements, see `Compatible Django / Python versions`_ table

Upgrade process
===============
We recommend upgrading one feature release at a time, even if your project is several versions behind the current one. This has a number of advantages over skipping directly to the newest release:

* If anything breaks as a result of the upgrade, you will know which version caused it, and will be able to troubleshoot accordingly;
* Deprecation warnings shown in the console output will notify you of any code changes you need to make before upgrading to the following version;
* Some releases make database schema changes that need to be reflected on your project by running ``./manage.py makemigrations`` - this is liable to fail if too many schema changes happen in one go.

Before upgrading to a new feature release:

* Check your project's console output for any deprecation warnings, and fix them where necessary;
* Check the new version's release notes, and the `Compatible Django / Python versions`_ table below, for any dependencies that need upgrading first;
* **IMPORTANT** Make a backup of your database. You may find yourself dropping and restoring your local database several times in order to get the django migrations to run correctly through the upgrades.

-----------
To upgrade
-----------
**Wagtail 2.0 Note:** If you are upgrading to Wagtail 2.0, there is an update script for the module paths! See the `Wagtail 2.0 Module Path Update Script`_ section below for more information.

* Update the ``wagtail`` line in your project's ``requirements.txt`` file to specify the latest patch release of the version you wish to install. For example, to upgrade to version 1.8.x, the line should read::

    wagtail>=1.8,<1.9

* Run:

  .. code-block:: console

      pip install -r requirements.txt
      ./manage.py makemigrations
      ./manage.py migrate

* Make any necessary code changes as directed in the "Upgrade considerations" section of the release notes.
* Test that your project is working as expected.

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

Upgrading directly to Wagtail 2:
================================
**WARNING:** You should first locally try to upgrade version by version to see if there are any major application issues before attempting to upgrade directly. 

----------------
Tips and Tricks:
----------------
During the deployment process, you may find that you want to try and upgrade directly to Wagtail 2 without having to do multiple deployments. In addition, when running python tests for migrations, your migrations will most likely fail as your test database is a new blank database that tests run from. They fail because your home migrations run a dependency that reference a Wagtail app migration that has not yet run. 

Locally upgrade environment:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Upgrade version of Wagtail to v2 in the requirements.txt
2. Run the update script: ``wagtail updatemodulepaths``
3. Run migrations ``./manage.py migrate``. This will go ahead and add all of the necessary migrations to your database. You won't need to run these migrations again.
4. Run tests ``./manage.py test``. You may find that migrations may fail at a specific migration, take note of that.
5. Add the failed migration from tests to the initial home migration dependency. To track down the correct app and run ``./manage.py showmigrations``. 
6. Run tests again ``./manage.py test``. At this point, tests should pass.

Deployment:
~~~~~~~~~~~
1. Create one branch that upgrades and disables migrations from python tests. Merge this first to deploy upgrade.
2. Create another branch that adds the necessary failed test dependency to your intial home migration. Merge this second and deploy. 

After following the 2 deployment steps above, that will upgrade you to the most recent version of Wagtail with passing tests and migrations. You wont have to do this again unless there is another major upgrade to wagtail.

We've Upgraded...what now?:
~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Take a good look at all of your custom built applications to see if they still work in Wagtail 2.
* Hallo vs Draftail: Since you cannot run both rich text editor libraries at the same time, you will need to choose between using Hallo or Draftail. HalloPlugins have been deprecated, and will be removed in Wagtail 1.14. So it would be best that you make the effort to attempt to transfer over to draftail now, this comes by default with Wagtail 2. 

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

