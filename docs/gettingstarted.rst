Getting Started
---------------

Using Vagrant (recommended for development)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Install `Vagrant`_ 1.1+
-  ``git clone git@github.com:torchbox/wagtaildemo.git``
-  ``cd wagtaildemo``
-  ``vagrant up``
-  ``vagrant ssh``
-  ``./manage.py createsuperuser``
-  ``./manage.py update_index``
-  ``./manage.py runserver 0.0.0.0:8000``
-  Edit your code locally, browse at `localhost:8111`_ and
   `localhost:8111/admin`_

Without Vagrant (recommended for production)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Install PostgreSQL, Redis, npm, CoffeeScript, LESS and Elasticsearch.
   You may find the demo site `installation script`_ helpful,
   particularly if you are running Debian or Ubuntu.
-  ``git clone git@github.com:torchbox/wagtaildemo.git``
-  ``cd wagtaildemo``
-  ``pip install -r requirements.txt``
-  ``createdb wagtaildemo``
-  ``./manage.py syncdb``
-  ``./manage.py migrate``
-  ``./manage.py runserver``

Hosted Elasticsearch
~~~~~~~~~~~~~~~~~~~~

Wagtail currently depends on `Elasticsearch`_. If you don't want to run
an Elasticsearch server in development or production, there are many
hosted services available, including `Searchly`_, who offer a free
account suitable for testing and development. To use Searchly:

-  Sign up for an account at `dashboard.searchly.com/users/sign\_up`_
-  Use your Searchly dashboard to create a new index, e.g. 'wagtaildemo'
-  Note the connection URL from your Searchly dashboard
-  Update ``WAGTAILSEARCH_ES_URLS`` and ``WAGTAILSEARCH_ES_INDEX`` in
   your local settings
-  Run ``./manage.py update_index``

.. _Vagrant: http://www.vagrantup.com/
.. _`localhost:8111`: http://localhost:8111
.. _`localhost:8111/admin`: http://localhost:8111/admin/
.. _installation script: https://github.com/torchbox/wagtaildemo/blob/master/etc/install/install.sh
.. _Elasticsearch: http://www.elasticsearch.org/
.. _Searchly: http://www.searchly.com/
.. _dashboard.searchly.com/users/sign\_up: https://dashboard.searchly.com/users/sign_up