Getting started
===============

.. note::
   These instructions assume familiarity with virtual environments and the
   `Django web framework <https://www.djangoproject.com/>`_.
   For more detailed instructions, see :doc:`tutorial`.
   To add Wagtail to an existing Django project, see :doc:`integrating_into_django`.


Dependencies needed for installation
------------------------------------

* `Python 3 <https://www.python.org/downloads/>`_
* **libjpeg** and **zlib**, libraries required for Django's **Pillow** library.
  See Pillow's `platform-specific installation instructions <https://pillow.readthedocs.org/en/latest/installation.html#external-libraries>`_.


Quick install
-------------

Run the following in a virtual environment of your choice:

.. code-block:: console

    $ pip install wagtail

(Installing outside a virtual environment may require ``sudo``.)

Once installed, Wagtail provides a command similar to Django's ``django-admin startproject`` to generate a new site/project:

.. code-block:: console

    $ wagtail start mysite

This will create a new folder ``mysite``, based on a template containing everything you need to get started.
More information on that template is available in
:doc:`the project template reference </reference/project_template>`.

Inside your ``mysite`` folder, run the setup steps necessary for any Django project:

.. code-block:: console

    $ pip install -r requirements.txt
    $ ./manage.py migrate
    $ ./manage.py createsuperuser
    $ ./manage.py runserver

Your site is now accessible at ``http://localhost:8000``, with the admin backend available at ``http://localhost:8000/admin/``.

This will set you up with a new stand-alone Wagtail project.
If you'd like to add Wagtail to an existing Django project instead, see :doc:`integrating_into_django`.

There are a few optional packages which are not installed by default but are recommended to improve performance or add features to Wagtail, including:

 * :doc:`Elasticsearch </advanced_topics/performance>`.
 * :ref:`image_feature_detection`.


.. toctree::
    :maxdepth: 1

    tutorial
    demo_site
    integrating_into_django
    the_zen_of_wagtail
