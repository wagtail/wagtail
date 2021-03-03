.. _redirects:

=========
Redirects
=========

.. module:: wagtail.contrib.redirects

The ``redirects`` module provides the models and user interface for managing arbitrary redirection between urls and ``Pages`` or other urls.

Installation
============

The ``redirects`` module is not enabled by default. To install it, add ``wagtail.contrib.redirects`` to ``INSTALLED_APPS`` and ``wagtail.contrib.redirects.middleware.RedirectMiddleware`` to ``MIDDLEWARE`` in your project's Django settings file.


.. code-block:: python

    INSTALLED_APPS = [
        # ...

        'wagtail.contrib.redirects',
    ]

    MIDDLEWARE = [
        # ...
        # all other django middlware first

        'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    ]

This app contains migrations so make sure you run the ``migrate`` django-admin command after installing.

Usage
=====

Once installed, a new menu item called "Redirects" should appear in the "Settings" menu. This is where you can add arbitrary redirects to your site.

Page model recipe of to have redirects created automatically when changing a page's slug, see :ref:`page_model_auto_redirects_recipe`.

For an editor's guide to the interface, see :ref:`managing_redirects`.


Management commands
===================

import_redirects
----------------

.. code-block:: console

    $ ./manage.py import_redirects

This command imports and creates redirects from a file supplied by the user.

Options:

- **src**
  This is the path to the file you wish to import redirects from.

- **site**
  This is the **site** for the site you wish to save redirects to.

- **permanent**
  If the redirects imported should be **permanent** (True) or not (False). It's True by default.

- **from**
  The column index you want to use as redirect from value.

- **to**
  The column index you want to use as redirect to value.

- **dry_run**
  Lets you run a import without doing any changes.

- **ask**
  Lets you inspect and approve each redirect before it is created.



The ``Redirect`` class
======================

.. automodule:: wagtail.contrib.redirects.models
.. autoclass:: Redirect

    .. automethod:: add_redirect
