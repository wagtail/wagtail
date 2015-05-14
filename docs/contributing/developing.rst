Development environment
-----------------------

Using the demo site & Vagrant
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We recommend using the `Wagtail demo site <https://github.com/torchbox/wagtaildemo/>`_ which uses Vagrant, as a basis for developing Wagtail itself.

Install the wagtaildemo following the instructions in the `wagtaildemo README <https://github.com/torchbox/wagtaildemo/blob/master/README.md>`_, then continue with the instructions below.

Clone a copy of `the Wagtail codebase <https://github.com/torchbox/wagtail>`_ alongside your demo site at the same level. So in the directory containing wagtaildemo, run::

    git clone https://github.com/torchbox/wagtail.git

Enable the Vagrantfile included with the demo - this ensures you can edit the Wagtail codebase from outside Vagrant::

    cd wagtaildemo
    cp Vagrantfile.local.example Vagrantfile.local

If you clone Wagtail's codebase to somewhere other than one level above, edit ``Vagrantfile.local`` to specify the alternate path.

Lastly, we tell Django to use your freshly cloned Wagtail codebase as the source of Wagtail CMS, not the pip-installed version that came with wagtaildemo::

    cp wagtaildemo/settings/local.py.example wagtaildemo/settings/local.py

Uncomment the lines from ``import sys`` onward, and edit the rest of ``local.py`` as appropriate.

If your VM is currently running, you'll then need to run ``vagrant halt`` followed by ``vagrant up`` for the changes to take effect.


Coding guidelines
~~~~~~~~~~~~~~~~~

* PEP8. We ask that all Python contributions adhere to the `PEP8 <http://www.python.org/dev/peps/pep-0008/>`_ style guide, apart from the restriction on line length (E501). The `pep8 tool <http://pep8.readthedocs.org/en/latest/>`_ makes it easy to check your code, e.g. ``pep8 --ignore=E501 your_file.py``.
* Python 2 and 3 compatibility. All contributions should support Python 2 and 3 and we recommend using the `six <https://pythonhosted.org/six/>`_ compatibility library (use the pip version installed as a dependency, not the version bundled with Django).
* Tests. Wagtail has a suite of tests, which we are committed to improving and expanding. We run continuous integration at `travis-ci.org/torchbox/wagtail <https://travis-ci.org/torchbox/wagtail>`_ to ensure that no commits or pull requests introduce test failures. If your contributions add functionality to Wagtail, please include the additional tests to cover it; if your contributions alter existing functionality, please update the relevant tests accordingly.


Running the unit tests
~~~~~~~~~~~~~~~~~~~~~~

In order to run Wagtail's test suite, you will need to install some dependencies first. We recommend installing these into a virtual environment.


**Setting up the virtual environment**

If you are using Python 3.3 or above, run the following commands in your shell
at the root of the Wagtail repo::

    pyvenv venv
    source venv/bin/activate
    python setup.py develop
    pip install -r requirements-dev.txt

For Python 2, you will need to install the ``virtualenv`` package and replace
the first line above with:

    virtualenv venv

**Running the tests**

With your virtual environment active, run the following command to run all the
tests::

    python runtests.py

**Running only some of the tests**

At the time of writing, Wagtail has nearly 1000 tests which takes a while to
run. You can run tests for only one part of Wagtail by passing in the path as
an argument to ``runtests.py``::

    python runtests.py wagtail.wagtailcore

**Testing against PostgreSQL**

By default, Wagtail tests against SQLite. If you need to test against a
different database, set the ``DATABASE_ENGINE`` environment variable to the
name of the Django database backend to test against::

    DATABASE_ENGINE=django.db.backends.postgresql_psycopg2 python runtests.py

This will create a new database called ``test_wagtail`` in PostgreSQL and run
the tests against it.

If you need to use a different user, password or host. Use the ``PGUSER``, ``PGPASSWORD`` and ``PGHOST`` environment variables.

**Testing Elasticsearch**

To test Elasticsearch, you need to have the ``elasticsearch`` package installed.

Once installed, Wagtail will attempt to connect to a local instance of
Elasticsearch (``http://localhost:9200``) and use the index ``test_wagtail``.

If your Elasticsearch instance is located somewhere else, you can set the
``ELASTICSEARCH_URL`` environment variable to point to its location::

    ELASTICSEARCH_URL=http://my-elasticsearch-instance:9200 python runtests.py

If you no longer want Wagtail to test against Elasticsearch, uninstall the
``elasticsearch`` package.
