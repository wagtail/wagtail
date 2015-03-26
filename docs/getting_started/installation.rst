============
Installation
============


Before you start
================

You can get basic Wagtail setup installed on your machine with only a few prerequisites. See the full  `Dependencies`_ list below.

There are various optional components that will improve the performance and feature set of Wagtail. Our recommended software stack includes the PostgreSQL database, Elasticsearch (for free-text searching), the OpenCV library (for image feature detection), and Redis (as a cache and message queue backend). This would be a lot to install in one go. For this reason we provide a virtual machine image to use with `Vagrant <http://www.vagrantup.com/>`__, with all of these components ready installed.

Whether you just want to try out the demo site, or you're ready to dive in and create a Wagtail site with all bells and whistles enabled, we strongly recommend the Vagrant approach. Nevertheless, if you're the sort of person who balks at the idea of downloading a whole operating system just to run a web app, we've got you covered too. Start from `Install Python`_.


Dependencies
============

Wagtail is based on the Django web framework and various other Python libraries. For the full list of absolutely required libraries, see `setup.py <https://github.com/torchbox/wagtail/blob/master/setup.py>`__.

Most of Wagtail's dependencies are pure Python and will install automatically using ``pip``, but there are a few native-code components that require further attention:

 * libsass-python (for compiling SASS stylesheets) - requires a C++ compiler and the Python development headers.
 * Pillow (for image processing) - additionally requires libjpeg and zlib.

On Debian or Ubuntu, these can be installed with the command::

    sudo apt-get install python-dev python-pip g++ libjpeg62-dev zlib1g-dev

Install Python
==============

If you haven't got Python installed yet, we recommend installing Python 3.4. You can download it here: https://www.python.org/downloads/


pip
---

Python 3.4 has this built in. If you are using Python 2.7 or 3.3, you will have to install PIP separately

See: https://pip.pypa.io/en/latest/installing.html


Virtual environments
--------------------

Python 3.3 and 3.4 has this built in. If you are using Python 2.7 you can install the ``virtualenv`` package using pip:

.. code-block:: bash

    pip install virtualenv


Install Wagtail
===============

The quickest way to install Wagtail is using pip. To get the latest stable version:

.. code-block:: bash

    pip install wagtail


If you are installing Wagtail differently (e.g. from the Git repository), you must run ``python setup.py install`` from the repository root. The above command will install all Wagtail dependencies.

To check that Wagtail can be seen by Python, type ``python`` in your shell then try to import ``wagtail`` from the prompt:

.. code-block:: python

    >>> import wagtail


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


Elasticsearch
-------------

Wagtail integrates with Elasticsearch to provide full-text searching of your content, both within the Wagtail interface and on your site's front-end. If Elasticsearch is not available, Wagtail will fall back to much more basic search functionality using database queries. Elasticsearch is pre-installed as part of the Vagrant virtual machine image; non-Vagrant users can use the `debian.sh <https://github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh>`__ or `ubuntu.sh <https://github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh>`__ installation scripts as a guide.

To enable Elasticsearch for your project, uncomment the ``elasticsearch`` line from your project's requirements.txt, and in ``myprojectname/settings/base.py``, uncomment the WAGTAILSEARCH_BACKENDS section. Then run::

    pip install -r requirements.txt
    ./manage.py update_index


Image feature detection
-----------------------
Wagtail can use the OpenCV computer vision library to detect faces and other features in images, and use this information to select the most appropriate centre point when cropping the image. OpenCV is pre-installed as part of the Vagrant virtual machine image, and Vagrant users can enable this by setting ``WAGTAILIMAGES_FEATURE_DETECTION_ENABLED`` to True in ``myprojectname/settings/base.py``. For installation outside of Vagrant, see :ref:`image_feature_detection`.
