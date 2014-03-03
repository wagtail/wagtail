Getting Started
---------------

Using Vagrant
~~~~~~~~~~~~~

 We provide a Vagrant box which includes all the dependencies for a fully-fledged Wagtail environment, bundled with a demonstration site containing a set of standard templates and page types. If you have a good internet connection we recommend the following steps, which will download the 650MB Vagrant box and make a running Wagtail instance available as the basis for your new site:

-  Install `Vagrant <http://www.vagrantup.com/>`_ 1.1+
-  Clone the demonstration site, create the Vagrant box and initialise Wagtail::

	git clone git@github.com:torchbox/wagtaildemo.git
	cd wagtaildemo
	vagrant up
	vagrant ssh
	# within the SSH session
	./manage.py createsuperuser
	./manage.py update_index
	./manage.py runserver 0.0.0.0:8000

-  This will make the app accessible on the host machine as `localhost:8111 <http://localhost:8111>`_ - you can access the Wagtail admin interface at `localhost:8111/admin <http://localhost:8111/admin>`_. The codebase is located on the host machine, exported to the VM as a shared folder; code editing and Git operations will generally be done on the host.

Without Vagrant
~~~~~~~~~~~~~~~

For production, or if you prefer not to use Vagrant, use the following steps to install Wagtail:

Required dependencies
=====================

-  `npm`_
-  `CoffeeScript`_
-  `Less`_
-  `pip`_

Optional dependencies
=====================

-  `PostgreSQL`_
-  `Elasticsearch`_

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
.. _npm: https://npmjs.org/
.. _CoffeeScript: http://coffeescript.org/
.. _Less: http://lesscss.org/
.. _Pip: https://github.com/pypa/pip
