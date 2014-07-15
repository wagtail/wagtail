.. _getting_started:

===============
Getting started
===============

Installing Wagtail
==================

From PyPI
---------

This is recommended for stability.

.. code-block:: bash

    pip install wagtail


From Github
-----------

This will give you the latest development version of Wagtail.

.. code-block:: bash

    pip install -e git://github.com/torchbox/wagtail.git#egg=wagtail


The ``wagtail-project`` command
===============================

.. versionadded:: 0.5

Once you have Wagtail installed on your host machine, you can use the ``wagtail-project`` command.

Usage:

.. code-block:: bash

    wagtail-project <project name>


This command will setup a skeleton Wagtail project with the following features installed:

 - A core app with migrations to replace the default Homepage
 - Base templates (base, 404, 500)
 - Vagrant configuration
 - Fabfile
 - Docs directory (with Sphinx configuration)
 - Split up settings configuration (different settings for dev and production)
 - Requirements


Where to look next
==================

.. toctree::
   :maxdepth: 2

   building_your_site/index
