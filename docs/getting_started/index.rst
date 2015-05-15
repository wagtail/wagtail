Getting started
===============

Wagtail is built on Django, so this document assumes you've already got the essentials installed. But if not, those essentials are:

 * `Python <https://wiki.python.org/moin/BeginnersGuide/Download>`_
 * `pip <https://pip.pypa.io/en/latest/installing.html>`_ (Note that pip is included by default with Python 2.7.9 and later and Python 3.4 and later)

We'd also strongly recommend:

 * `Virtualenv <https://virtualenv.pypa.io/en/latest/installation.html>`_


With the above installed and enabled, the quickest way to install wagtail is::

    pip install wagtail

Once installed, Wagtail provides a command similar to Django's ``django-admin startproject``::

    wagtail start mysite

This will create a new folder ``mysite``, based on a template containing all you need to get started. More information on that template is available :doc:`here </reference/project_template>`.

Inside your ``mysite`` folder, we now just run the setup steps necessary for any Django project::

    ./manage.py migrate
    ./manage.py createsuperuser
    ./manage.py runserver

Your site is now accessible at ``http://localhost:8000``, with the admin backend available at ``http://localhost:8000/admin/``.


There are a few optional packages which are not installed by default but are recommended to improve performance or add features to Wagtail:

 * :doc:`Elasticsearch </howto/performance>`.
 * :ref:`image_feature_detection`.


.. toctree::
    :maxdepth: 2

    demo_site
