Developing Wagtail
-----------------------

Issues
~~~~~~

The easiest way to contribute to Wagtail is to tell us how to improve it! First, check to see if your bug or feature request has already been submitted at `github.com/torchbox/wagtail/issues <https://github.com/torchbox/wagtail/issues>`_. If it has, and you have some supporting information which may help us deal with it, comment on the existing issue. If not, please `create a new one <https://github.com/torchbox/wagtail/issues/new>`_, providing as much relevant context as possible. For example, if you're experiencing problems with installation, detail your environment and the steps you've already taken. If something isn't displaying correctly, tell us what browser you're using, and include a screenshot if possible.

Pull requests
~~~~~~~~~~~~~

If you're a Python or Django developer, `fork <https://github.com/torchbox/wagtail/>`_ and get stuck in! Send us a useful pull request and we'll post you a `t-shirt <https://twitter.com/WagtailCMS/status/432166799464210432/photo/1>`_. We welcome all contributions, whether they solve problems which are specific to you or they address existing issues. If you're stuck for ideas, pick something from the `issue list <https://github.com/torchbox/wagtail/issues?state=open>`_, or email us directly on `hello@wagtail.io <mailto:hello@wagtail.io>`_ if you'd like us to suggest something!

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

Styleguide
~~~~~~~~~~

Developers working on the Wagtail UI or creating new UI components may wish to test their work against our Styleguide, which is provided as the contrib module "wagtailstyleguide".

To install the styleguide module on your site, add it to the list of ``INSTALLED_APPS`` in your settings:

.. code-block:: python

	INSTALLED_APPS = (
	   ...
	   'wagtail.contrib.wagtailstyleguide',
	   ...
	)

At present the styleguide is static: new UI components must be added to it manually, and there are no hooks into it for other modules to use. We hope to support hooks in the future.

The styleguide doesn't currently provide examples of all the core interface components; notably the Page, Document, Image and Snippet chooser interfaces are not currently represented.


Translations
~~~~~~~~~~~~

Wagtail has internationalisation support so if you are fluent in a non-English language you can contribute by localising the interface.

Our preferred way to submit or contribute to a language translation is via `Transifex <https://www.transifex.com/projects/p/wagtail/>`_.

Other contributions
~~~~~~~~~~~~~~~~~~~

We welcome contributions to all aspects of Wagtail. If you would like to improve the design of the user interface, or extend the documentation, please submit a pull request as above. If you're not familiar with Github or pull requests, `contact us directly <mailto:hello@wagtail.io>`_ and we'll work something out.
