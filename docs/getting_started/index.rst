Getting started
===============

Wagtail is built on the `Django web framework <https://www.djangoproject.com/>`_, so this document assumes you've already got the essentials installed. But if not, those essentials are:

 * `Python <https://www.python.org/downloads/>`_
 * `pip <https://pip.pypa.io/en/latest/installing.html>`_ (Note that pip is included by default with Python 2.7.9 and later and Python 3.4 and later)

We'd also recommend Virtualenv, which provides isolated Python environments:

 * `Virtualenv <https://virtualenv.pypa.io/en/latest/installation.html>`_


Before we install Wagtail we should install Pillow for image manipulation. Before you run ``pip install Pillow`` note that most platforms require you install additional libraries first: `Platform-specific installation instructions <http://pillow.readthedocs.org/en/latest/installation.html#os-x-installation>`_

With the above installed, the quickest way to install Wagtail is::

    pip install wagtail

(``sudo`` may be required if installing system-wide or without virtualenv)

Once installed, Wagtail provides a command similar to Django's ``django-admin startproject`` which stubs out a new site/project::

    wagtail start mysite

This will create a new folder ``mysite``, based on a template containing all you need to get started. More information on that template is available :doc:`here </reference/project_template>`.

Inside your ``mysite`` folder, we now just run the setup steps necessary for any Django project::

    pip install -r requirements.txt
    ./manage.py migrate
    ./manage.py createsuperuser
    ./manage.py runserver

Your site is now accessible at ``http://localhost:8000``, with the admin backend available at ``http://localhost:8000/admin/``.


There are a few optional packages which are not installed by default but are recommended to improve performance or add features to Wagtail, including:

 * :doc:`Elasticsearch </advanced_topics/performance>`.
 * :ref:`image_feature_detection`.


.. toctree::
    :maxdepth: 2

    tutorial
    demo_site
