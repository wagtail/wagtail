Getting Started
---------------

On Ubuntu
~~~~~~~~~

If you have a fresh instance of Ubuntu 13.04 or later, you can install Wagtail,
along with a demonstration site containing a set of standard templates and page
types, in one step. As the root user::

  curl -O https://wagtail.io/ubuntu.sh; bash ubuntu.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh>`_.

Once you've experimented with the demo app and are ready to build your pages via your own app you can `remove the demo app`_ if you choose.

On Debian
~~~~~~~~~

If you have a fresh instance of Debian 7, you can install Wagtail, along with a
demonstration site containing a set of standard templates and page types, in one
step. As the root user::

  curl -O https://wagtail.io/debian.sh; bash debian.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh>`_.

Once you've experimented with the demo app and are ready to build your pages via your own app you can `remove the demo app`_ if you choose.

On OS X
~~~~~~~

Install `pip <http://pip.readthedocs.org/en/latest/installing.html>`_ and `virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/>`_ if you don't have them already. Then, in your terminal::

    mkvirtualenv wagtaildemo
    git clone https://github.com/torchbox/wagtaildemo.git
    cd wagtaildemo
    pip install -r requirements/dev.txt

Edit ``wagtaildemo/settings/base.py``, changing ENGINE to django.db.backends.sqlite3 and NAME to wagtail.db. Finally, setup the database and run the local server::

    ./manage.py syncdb
    ./manage.py migrate
    ./manage.py runserver

Using Vagrant
~~~~~~~~~~~~~

We provide a Vagrant box which includes all the dependencies for a fully-fledged
Wagtail environment, bundled with a demonstration site containing a set of
standard templates and page types. If you have a good internet connection we recommend
the following steps, which will download the 650MB Vagrant box and make a running
Wagtail instance available as the basis for your new site:

-  Install `Vagrant <http://www.vagrantup.com/>`_ 1.1+
-  Clone the demonstration site, create the Vagrant box and initialise Wagtail::

	git clone https://github.com/torchbox/wagtaildemo.git
	cd wagtaildemo
	vagrant up
	vagrant ssh
	# within the SSH session
	./manage.py createsuperuser
	./manage.py update_index
	./manage.py runserver 0.0.0.0:8000

-  This will make the app accessible on the host machine as
`localhost:8111 <http://localhost:8111>`_ - you can access the Wagtail admin
interface at `localhost:8111/admin <http://localhost:8111/admin>`_. The codebase
is located on the host machine, exported to the VM as a shared folder; code
editing and Git operations will generally be done on the host.

Using Docker
~~~~~~~~~~~~

`@oyvindsk <https://github.com/oyvindsk>`_ has built a Dockerfile for the Wagtail demo. Simply run::

	docker run -p 8000:8000 -d oyvindsk/wagtail-demo

then access the site at http://your-ip:8000 and the admin
interface at http://your-ip:8000/admin using admin / test.

See https://index.docker.io/u/oyvindsk/wagtail-demo/ for more details.

Other platforms
~~~~~~~~~~~~~~~

If you're not using Ubuntu or Debian, or if you prefer to install Wagtail manually,
use the following steps:

Required dependencies
=====================

-  `pip <https://github.com/pypa/pip>`_
-  `libjpeg <http://ijg.org/>`_
-  `libxml2 <http://xmlsoft.org/>`_
-  `libxslt <http://xmlsoft.org/XSLT/>`_
-  `zlib <http://www.zlib.net/>`_

Optional dependencies
=====================

-  `PostgreSQL`_
-  `Elasticsearch`_
-  `Redis`_

Installation
============

With PostgreSQL running (and configured to allow you to connect as the
'postgres' user - if not, you'll need to adjust the ``createdb`` line
and the database settings in wagtaildemo/settings/base.py accordingly),
run the following commands::

    git clone https://github.com/torchbox/wagtaildemo.git
    cd wagtaildemo
    pip install -r requirements/dev.txt
    createdb -Upostgres wagtaildemo
    ./manage.py syncdb
    ./manage.py migrate
    ./manage.py runserver

SQLite support
==============

SQLite is supported as an alternative to PostgreSQL - update the DATABASES setting
in wagtaildemo/settings/base.py to use 'django.db.backends.sqlite3', as you would
with a regular Django project.

.. _Wagtail: http://wagtail.io
.. _VirtualBox: https://www.virtualbox.org/
.. _the Wagtail codebase: https://github.com/torchbox/wagtail
.. _PostgreSQL: http://www.postgresql.org
.. _Elasticsearch: http://www.elasticsearch.org
.. _Redis: http://redis.io/

_`Remove the demo app`
~~~~~~~~~~~~~~~~~~~~~~

Once you've experimented with the demo app and are ready to build your pages via your own app you can remove the demo app if you choose.

``PROJECT_ROOT`` should be where your project is located (e.g. /usr/local/django) and ``PROJECT`` is the name of your project (e.g. mywagtail)::

    export PROJECT_ROOT=/usr/local/django
    export PROJECT=mywagtail
    cd $PROJECT_ROOT/$PROJECT
    ./manage.py sqlclear demo | psql -Upostgres $PROJECT -f -
    psql -Upostgres $PROJECT << EOF
    BEGIN;
    DELETE FROM wagtailcore_site WHERE root_page_id IN (SELECT id FROM wagtailcore_page WHERE content_type_id IN (SELECT id FROM django_content_type where app_label='demo'));
    DELETE FROM wagtailcore_page WHERE content_type_id IN (SELECT id FROM django_content_type where app_label='demo');
    DELETE FROM auth_permission WHERE content_type_id IN (SELECT id FROM django_content_type where app_label='demo');
    DELETE FROM django_content_type WHERE app_label='demo';
    DELETE FROM wagtailimages_rendition;
    DELETE FROM wagtailimages_image;
    COMMIT;
    EOF
    rm -r demo media/images/* media/original_images/*
    perl -pi -e"s/('demo',|WAGTAILSEARCH_RESULTS_TEMPLATE)/#\1/" $PROJECT/settings/base.py
