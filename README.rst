.. image:: https://travis-ci.org/torchbox/wagtail.png?branch=master
    :target: https://travis-ci.org/torchbox/wagtail

.. image:: https://coveralls.io/repos/torchbox/wagtail/badge.png?branch=master&zxcv1
    :target: https://coveralls.io/r/torchbox/wagtail?branch=master

.. image:: https://pypip.in/v/wagtail/badge.png?zxcv
    :target: https://crate.io/packages/wagtail/

Wagtail CMS
===========

.. image:: http://i.imgur.com/4pbWQ35.png

Wagtail is a Django content management system built originally for the `Royal College of Art <http://www.rca.ac.uk/>`_ and focused on flexibility and user experience. Its features include:

* A fast, attractive editor interface
* Complete control over design with standard Django templates
* Configure content types through standard Django models
* Tightly integrated search (with an `Elasticsearch <http://www.elasticsearch.org/>`_ backend for production)
* Strong document and image management
* Wide support for embedded content
* Simple, configurable permissions
* Support for tree-based content organisation
* Optional preview->submit->approve workflow
* Fast out of the box. `Varnish <https://www.varnish-cache.org/>`_-friendly if you need it
* A simple `form builder <http://docs.wagtail.io/en/latest/form_builder.html>`_
* Optional `static site generation <http://docs.wagtail.io/en/latest/static_site_generation.html>`_
* Excellent `test coverage <https://coveralls.io/r/torchbox/wagtail?branch=master>`_

Find out more at `wagtail.io <http://wagtail.io/>`_.

Got a question? Ask it on our `Google Group <https://groups.google.com/forum/#!forum/wagtail>`_.

Getting started
~~~~~~~~~~~~~~~
* To get you up and running quickly, we've provided a demonstration site with all the configuration in place, at `github.com/torchbox/wagtaildemo <https://github.com/torchbox/wagtaildemo/>`_; see the `README <https://github.com/torchbox/wagtaildemo/blob/master/README.md>`_ for installation instructions.
* See the `Getting Started <http://wagtail.readthedocs.org/en/latest/gettingstarted.html#getting-started>`_ docs for installation (with the demo app) on a fresh Debian/Ubuntu box with production-ready dependencies, on OS X and on a Vagrant box.
* `Serafeim Papastefanos <https://github.com/spapas>`_ has written a `tutorial <http://spapas.github.io/2014/02/13/wagtail-tutorial/>`_ with all the steps to build a simple Wagtail site from scratch.
* We've also provided a skeletal django-template to get started on a blank site: https://github.com/torchbox/wagtail-template

Documentation
~~~~~~~~~~~~~
Available at `wagtail.readthedocs.org <http://wagtail.readthedocs.org/>`_ and always being updated.

Compatibility
~~~~~~~~~~~~~
Wagtail supports Django 1.6.2+ on Python 2.6, 2.7, 3.2, 3.3 and 3.4.

Django 1.7 support is in progress pending further release candidate testing.

Wagtail's dependencies are summarised at `requirements.io <https://requires.io/github/torchbox/wagtail/requirements>`_.

Contributing
~~~~~~~~~~~~
If you're a Python or Django developer, fork the repo and get stuck in!

We suggest you start by checking the `Help develop me! <https://github.com/torchbox/wagtail/issues?labels=Help+develop+me%21>`_ label.

Send us a useful pull request and we'll post you a `t-shirt <https://twitter.com/WagtailCMS/status/432166799464210432/photo/1>`_.

