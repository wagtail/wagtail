============
Installation
============


Before you start
================

A basic Wagtail setup can be installed on your machine with only a few prerequisites - see `A basic Wagtail installation`_. However, there are various optional components that will improve the performance and feature set of Wagtail, and our recommended software stack includes the PostgreSQL database, ElasticSearch (for free-text searching), the OpenCV library (for image feature detection), and Redis (as a cache and message queue backend). This would be a lot to install in one go, and for this reason, we provide a virtual machine image, for use with `Vagrant <http://www.vagrantup.com/>`__, with all of these components ready installed.

Whether you just want to try out the demo site, or you're ready to dive in and create a Wagtail site with all bells and whistles enabled, we strongly recommend the Vagrant approach. Nevertheless, if you're the sort of person who balks at the idea of downloading a whole operating system just to run a web app, we've got you covered too. Start from `A basic Wagtail installation`_ below.


Install Python
==============

We recommend installing Python 3.4, but Wagtail also works with Python 2.7 and 3.3.



Install Wagtail
===============

``pip install wagtail``


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


Alternative installation methods
================================

Ubuntu
------

If you have a fresh instance of Ubuntu 13.04 or later, you can install Wagtail,
along with a demonstration site containing a set of standard templates and page
types, in one step. As the root user::

  curl -O https://raw.githubusercontent.com/torchbox/wagtail/master/scripts/install/ubuntu.sh; bash ubuntu.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh>`_.


Debian
------

If you have a fresh instance of Debian 7, you can install Wagtail, along with a
demonstration site containing a set of standard templates and page types, in one
step. As the root user::

  curl -O https://raw.githubusercontent.com/torchbox/wagtail/master/scripts/install/debian.sh; bash debian.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh>`_.


Docker
------

`@oyvindsk <https://github.com/oyvindsk>`_ has built a Dockerfile for the Wagtail demo. Simply run::

	docker run -p 8000:8000 -d oyvindsk/wagtail-demo

then access the site at http://your-ip:8000 and the admin
interface at http://your-ip:8000/admin using admin / test.

See https://index.docker.io/u/oyvindsk/wagtail-demo/ for more details.
