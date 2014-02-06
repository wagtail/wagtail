Running the Test Suite
======================

``django-treebeard`` includes a comprehensive test suite. It is highly
recommended that you run and update the test suite when you send patches.

py.test
-------

You will need `pytest`_ to run the test suite.

To run the test suite:

.. code-block:: console

    $ py.test

You can use all the features and plugins of pytest this way.

By default the test suite will run using a sqlite3 database in RAM, but you can
change this setting environment variables:

.. option:: DATABASE_ENGINE
.. option:: DATABASE_NAME
.. option:: DATABASE_USER
.. option:: DATABASE_PASSWORD
.. option:: DATABASE_HOST
.. option:: DATABASE_PORT

   Sets the database settings to be used by the test suite. Useful if you
   want to test the same database engine/version you use in production.


tox
---

``django-treebeard`` uses `tox`_ to run the test suite in all the supported
environments:

    - py26-dj14-sqlite
    - py26-dj14-mysql
    - py26-dj14-pgsql
    - py26-dj15-sqlite
    - py26-dj15-mysql
    - py26-dj15-pgsql
    - py26-dj16-sqlite
    - py26-dj16-mysql
    - py26-dj16-pgsql
    - py27-dj14-sqlite
    - py27-dj14-mysql
    - py27-dj14-pgsql
    - py27-dj15-sqlite
    - py27-dj15-mysql
    - py27-dj15-pgsql
    - py32-dj15-sqlite
    - py32-dj15-pgsql
    - py33-dj15-sqlite
    - py33-dj15-pgsq
    - py27-dj16-sqlite
    - py27-dj16-mysql
    - py27-dj16-pgsql
    - py32-dj16-sqlite
    - py32-dj16-pgsql
    - py33-dj16-sqlite
    - py33-dj16-pgsql


This means that the test suite will run 26 times to test every
environment supported by ``django-treebeard``. This takes a long time.
If you want to test only one or a few environments, please use the `-e`
option in `tox`_, like:

.. code-block:: console

    $ tox -e py33-dj16-pgsql


.. _pytest: http://pytest.org/
.. _coverage: http://nedbatchelder.com/code/coverage/
.. _tox: http://codespeak.net/tox/
