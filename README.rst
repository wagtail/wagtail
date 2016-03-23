.. image:: https://api.travis-ci.org/torchbox/wagtail.svg?branch=master
    :target: https://travis-ci.org/torchbox/wagtail
.. image:: https://img.shields.io/pypi/l/wagtail.svg
    :target: https://pypi.python.org/pypi/wagtail/
.. image:: https://img.shields.io/pypi/v/wagtail.svg
    :target: https://crate.io/packages/wagtail/
.. image:: https://coveralls.io/repos/torchbox/wagtail/badge.svg?branch=master
    :target: https://coveralls.io/r/torchbox/wagtail?branch=master

Wagtail CMS
===========

Wagtail is a content management system built on Django. It's focused on user experience,
and offers precise control for designers and developers.

.. image:: http://i.imgur.com/U5MDa0l.jpg
   :width: 728 px

Features
~~~~~~~~

* A fast, attractive interface for authors and editors
* Complete control over design with standard Django templates
* Configure content types through standard Django models
* Fast out of the box. Cache-friendly if you need it
* Tightly integrated search
* Strong document and image management
* Wide support for embedded content
* Straightforward integration with existing Django apps
* Simple, configurable permissions
* Workflow support
* An extensible `form builder <http://docs.wagtail.io/en/latest/reference/contrib/forms.html>`_
* Multi-site and multi-language support
* Optional `static site generation <http://docs.wagtail.io/en/latest/reference/contrib/staticsitegen.html>`_
* Excellent `test coverage <https://coveralls.io/r/torchbox/wagtail?branch=master>`_

Find out more at `wagtail.io <http://wagtail.io/>`_.

Getting started
~~~~~~~~~~~~~~~

.. code-block:: sh

    pip install wagtail
    wagtail start mysite
    cd mysite
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver

then sign in at http://127.0.0.1:8000/admin/

For detailed installation and setup docs, see `docs.wagtail.io <http://docs.wagtail.io/>`_.

Who's using it?
~~~~~~~~~~~~~~~
`madewithwagtail.org <http://madewithwagtail.org>`_ lists some of the public Wagtail sites we know about; please `add your own <http://madewithwagtail.org/submit/>`_.

Documentation
~~~~~~~~~~~~~
`docs.wagtail.io <http://docs.wagtail.io/>`_ is the full reference for Wagtail, and includes guides for developers, designers and editors, alongside release notes and our roadmap.

Community Support
~~~~~~~~~~~~~~~~~
Ask your questions on our `Wagtail support group <https://groups.google.com/forum/#!forum/wagtail>`_.

Commercial Support
~~~~~~~~~~~~~~~~~~
Wagtail is sponsored by `Torchbox <https://torchbox.com/>`_. If you need help implementing or hosting Wagtail, please contact us: hello@torchbox.com.

Compatibility
~~~~~~~~~~~~~
Wagtail supports Django 1.8.1+ on Python 2.7, 3.3, 3.4 and 3.5. Supported database backends are PostgreSQL, MySQL and SQLite.

Contributing
~~~~~~~~~~~~
If you're a Python or Django developer, fork the repo and get stuck in! We run a separate group for developers of Wagtail itself at https://groups.google.com/forum/#!forum/wagtail-developers (please note that this is not for support requests).

You might like to start by reviewing the `coding guidelines <http://docs.wagtail.io/en/latest/contributing/developing.html#coding-guidelines>`_ and checking issues with the `Ready to develop <https://github.com/torchbox/wagtail/issues?q=is%3Aopen+is%3Aissue+label%3A%22Ready+to+develop%21%22>`_ label.

Send us a particularly useful pull request and we'll post you a `t-shirt <https://twitter.com/WagtailCMS/status/432166799464210432/photo/1>`_.

We also welcome translations for Wagtail's interface. Translation work should be submitted through `Transifex <https://www.transifex.com/projects/p/wagtail/>`_.
