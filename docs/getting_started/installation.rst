============
Installation
============


Before you start
================

A basic Wagtail setup can be installed on your machine with only a few prerequisites - see `A basic Wagtail installation`_. However, there are various optional components that will improve the performance and feature set of Wagtail, and our recommended software stack includes the PostgreSQL database, ElasticSearch (for free-text searching), the OpenCV library (for image feature detection), and Redis (as a cache and message queue backend). This would be a lot to install in one go, and for this reason, we provide a virtual machine image, for use with `Vagrant <http://www.vagrantup.com/>`__, with all of these components ready installed.

Whether you just want to try out the demo site, or you're ready to dive in and create a Wagtail site with all bells and whistles enabled, we strongly recommend the Vagrant approach. Nevertheless, if you're the sort of person who balks at the idea of downloading a whole operating system just to run a web app, we've got you covered too. Start from `A basic Wagtail installation`_ below.


Install Python
==============

If you haven't got Python installed yet, we recommend installing Python 3.4. You can find the download for it here: https://www.python.org/downloads/


pip
---

Python 3.4 has this built in. If you are using Python 2.7 or 3.3, you will have to install PIP separately

See: https://pip.pypa.io/en/latest/installing.html


Virtual environments
--------------------

Python 3.3 and 3.4 has this built in. If you are using Python 2.7 you will have to install the ``virtualenv`` package from pip:

.. code-block:: bash

    pip install virtualenv


Install Wagtail
===============

Wagtail is available as a pip-installable package. To get the latest stable version:

.. code-block:: bash

    pip install wagtail


To check that Wagtail can be seen by Python. Type ``python`` in your shell then try to import ``wagtail`` from the prompt:

.. code-block:: python

    >>> import wagtail
    >>> print(wagtail.get_version())
    0.9


Optional extras
===============

For the best possible performance and feature set, we recommend setting up the following components. If you're using Vagrant, these are provided as part of the virtual machine image and just need to be enabled in the settings for your project. If you're using Wagtail without Vagrant, this will involve additional installation.


PostgreSQL
----------
PostgreSQL is a mature database engine suitable for production use, and is recommended by the Django development team. Non-Vagrant users will need to install the PostgreSQL development headers in addition to Postgres itself; on Debian or Ubuntu, this can be done with the following command::

    sudo apt-get install postgresql postgresql-server-dev-all

To enable Postgres for your project, uncomment the ``psycopg2`` line from your project's requirements.txt, and in ``myprojectname/settings/base.py``, uncomment the DATABASES section for PostgreSQL, commenting out the SQLite one instead. Then run::

    pip install -r requirements.txt
    createdb -Upostgres myprojectname
    ./manage.py migrate
    ./manage.py createsuperuser

This assumes that your PostgreSQL instance is configured to allow you to connect as the 'postgres' user - if not, you'll need to adjust the ``createdb`` line and the database settings in settings/base.py accordingly.


ElasticSearch
-------------

Wagtail integrates with ElasticSearch to provide full-text searching of your content, both within the Wagtail interface and on your site's front-end. If ElasticSearch is not available, Wagtail will fall back to much more basic search functionality using database queries. ElasticSearch is pre-installed as part of the Vagrant virtual machine image; non-Vagrant users can use the `debian.sh <https://github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh>`__ or `ubuntu.sh <https://github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh>`__ installation scripts as a guide.

To enable ElasticSearch for your project, uncomment the ``elasticsearch`` line from your project's requirements.txt, and in ``myprojectname/settings/base.py``, uncomment the WAGTAILSEARCH_BACKENDS section. Then run::

    pip install -r requirements.txt
    ./manage.py update_index


Image feature detection
-----------------------
Wagtail can use the OpenCV computer vision library to detect faces and other features in images, and use this information to select the most appropriate centre point when cropping the image. OpenCV is pre-installed as part of the Vagrant virtual machine image, and Vagrant users can enable this by setting ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` to True in ``myprojectname/settings/base.py``. For installation outside of Vagrant, see :ref:`image_feature_detection`.
