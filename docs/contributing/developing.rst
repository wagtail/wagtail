Development
-----------

Setting up a local copy of `the Wagtail git repository <https://github.com/torchbox/wagtail>`_ is slightly more involved than running a release package of Wagtail, as it requires `Node.js <https://nodejs.org/>`_ and NPM for building Javascript and CSS assets. (This is not required when running a release version, as the compiled assets are included in the release package.)

If you're happy to develop on a virtual machine, the `vagrant-wagtail-develop <https://github.com/torchbox/vagrant-wagtail-develop>`_ setup script is the fastest way to get up and running. This will provide you with a running instance of the `Wagtail demo site <https://github.com/torchbox/wagtaildemo/>`_, with the Wagtail and wagtaildemo codebases available as shared folders for editing on your host machine.

(Build scripts for other platforms would be very much welcomed - if you create one, please let us know via the `Wagtail Developers group <https://groups.google.com/forum/#!forum/wagtail-developers>`_!)

If you'd prefer to set up all the components manually, read on. These instructions assume that you're familiar with using pip and virtualenv to manage Python packages.


Setting up the Wagtail codebase
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Node.js, any version between v0.10.x and v0.12.x. Instructions for installing Node.js can be found on the `Node.js download page <https://nodejs.org/download/>`_. You will also need to install the **libjpeg** and **zlib** libraries, if you haven't done so already - see Pillow's `platform-specific installation instructions <http://pillow.readthedocs.org/en/latest/installation.html#external-libraries>`_.

Clone a copy of `the Wagtail codebase <https://github.com/torchbox/wagtail>`_:

.. code-block:: sh

    git clone https://github.com/torchbox/wagtail.git
    cd wagtail

With your preferred virtualenv activated, install the Wagtail package in development mode:

.. code-block:: sh

    python setup.py develop

Install the tool chain for building static assets:

.. code-block:: sh

    npm install

Compile the assets:

.. code-block:: sh

    npm run build

Any Wagtail sites you start up in this virtualenv will now run against this development instance of Wagtail. We recommend using the `Wagtail demo site <https://github.com/torchbox/wagtaildemo/>`_ as a basis for developing Wagtail.

Development dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

Developing Wagtail requires additional Python modules for testing and documentation.

The list of dependencies is in the Wagtail root directory in ``requirements-dev.txt`` and can be installed thus, from the Wagtail codebase root directory::

    pip install -r requirements-dev.txt


.. _testing:

Testing
~~~~~~~

From the root of the Wagtail codebase, run the following command to run all the tests::

    python runtests.py

**Running only some of the tests**

At the time of writing, Wagtail has well over 1000 tests, which takes a while to
run. You can run tests for only one part of Wagtail by passing in the path as
an argument to ``runtests.py``::

    python runtests.py wagtail.wagtailcore

**Testing against PostgreSQL**

By default, Wagtail tests against SQLite. You can switch to using PostgreSQL by
using the ``--postgres`` argument::

    python runtests.py --postgres

If you need to use a different user, password or host. Use the ``PGUSER``, ``PGPASSWORD`` and ``PGHOST`` environment variables.

**Testing against a different database**

If you need to test against a different database, set the ``DATABASE_ENGINE``
environment variable to the name of the Django database backend to test against::

    DATABASE_ENGINE=django.db.backends.mysql python runtests.py

This will create a new database called ``test_wagtail`` in MySQL and run
the tests against it.

**Testing Elasticsearch**

You can test Wagtail against Elasticsearch by passing the ``--elasticsearch``
argument to ``runtests.py``::

    python runtests.py --elasticsearch


Wagtail will attempt to connect to a local instance of Elasticsearch
(``http://localhost:9200``) and use the index ``test_wagtail``.

If your Elasticsearch instance is located somewhere else, you can set the
``ELASTICSEARCH_URL`` environment variable to point to its location::

    ELASTICSEARCH_URL=http://my-elasticsearch-instance:9200 python runtests.py --elasticsearch

Compiling static assets
~~~~~~~~~~~~~~~~~~~~~~~

All static assets such as JavaScript, CSS, images, and fonts for the Wagtail admin are compiled from their respective sources by ``gulp``. The compiled assets are not committed to the repository, and are compiled before packaging each new release. Compiled assets should not be submitted as part of a pull request.

To compile the assets, run:

.. code-block:: sh

    npm run build

This must be done after every change to the source files. To watch the source files for changes and then automatically recompile the assets, run:

.. code-block:: sh

    npm start
