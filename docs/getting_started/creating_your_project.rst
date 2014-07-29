=====================
Creating your project
=====================

.. contents:: Contents
    :local:


The ``wagtail-project`` command
===============================

The easiest way to start a new project with wagtail is to use the ``wagtail-project`` command. This command works the same way as ``django-admin.py startproject`` except that the produced project is pre-configured for Wagtail. It also contains some useful extras which we will look into in the next section.

To create a project, cd into a directory where you would like to create your project and run the following command:

 .. code-block:: bash

    wagtail-project mysite


The project
===========

Lets look at what ``wagtail-project`` created::

    mysite/
        docs/
            Makefile
            conf.py
            index.rst
            deploy.rst
            install.rst
        mysite/
            core/
            mysite/
                settings/
                    base.py
                    dev.py
                    production.py
            static/
            templates/
                base.html
                404.html
                500.html
            manage.py
        vagrant/
            provision.sh
        Vagrantfile
        fabfile.py
        readme.rst
        requirements.txt
        

The "core" app
----------------

Location: ``/mysite/core/``

This app is here to help get you started quicker by providing a ``HomePage`` model with migrations to create one when you first setup your app.


Default templates and static files
----------------------------------

Location: ``/mysite/templates/`` and ``/mysite/static/``

The templates directory contains ``base.html``, ``404.html`` and ``500.html``. These files are very commonly needed on Wagtail sites to they have been added into the template.

The static directory contains an empty javascript and sass file. Wagtail uses ``django-compressor`` for compiling and compressing static files. For more information, see: `Django Compressor Documentation <http://django-compressor.readthedocs.org/en/latest/>`_


Vagrant configuration
---------------------

Location: ``/Vagrantfile`` and ``/vagrant/``

If you have Vagrant installed, these files let you easily setup a development environment with PostgreSQL, Elasticsearch and Redis inside a virtual machine.

See below section `With Vagrant`_ for info on how to use Vagrant in development

If you do not want to use Vagrant, you can just delete these files.


The "docs" directory
----------------------

Location: ``/docs``

The docs directory contains Sphinx configuration, a Makefile and some starter documentation.

Docs are written in ReStructuredText and built by Sphinx.

To build the docs, make sure you have Sphinx installed, cd to the docs directory and run ``make haml``.


Django settings
---------------

Location: ``/mysite/mysite/settings/``

The Django settings files are split up into ``base.py``, ``dev.py``, ``production.py`` and ``local.py``.

.. glossary::

    ``base.py``

        This file is for global settings that will be used in both development and production. Aim to keep most of your configuration in this file.

    ``dev.py``

        This file is for settings that will only be used by developers. For example: ``DEBUG = True``

    ``production.py``

        This file is for settings that will only run on a production server. For example: ``DEBUG = False``

    ``local.py``

        This file is used for settings local to a particular machine. This file should never be tracked by a version control system.

        .. tip::

            On production servers, we recommend that you only store secrets in local.py (such as API keys and passwords). This can save you headaches in the future if you are ever trying to debug why a server is behaving badly. If you are using multiple servers which need different settings then we recommend that you create a different ``production.py`` file for each one.


Getting it running
==================


With Vagrant
------------

This is the easiest way to get the project running. Vagrant runs your project locally in a virtual machine so you can use PostgreSQL/Elasticsearch/Redis in development without having to install them on your host machine. If you haven't yet installed Vagrant, see: `Installing Vagrant <https://docs.vagrantup.com/v2/installation/>`_.


To setup the Vagrant box, run the following commands

 .. code-block:: bash

    vagrant up # This may take some time on first run
    vagrant ssh
    # within the ssh session
    dj createsuperuser
    djrun


If you now visit http://localhost:8111 you should see a very basic "Welcome to your new Wagtail site!" page.

You can browse the Wagtail admin interface at: http://localhost:8111/admin

You can read more about how Vagrant works at: https://docs.vagrantup.com/v2/


.. topic:: The ``dj`` and ``djrun`` aliases

    When using Vagrant, the Wagtail template provides two aliases: ``dj`` and ``djrun``.

    ``dj`` is short for ``python manage.py`` so you can use it to reduce typing. For example: ``python manage.py syncdb`` becomes ``dj syncdb``.

    ``djrun`` is short for ``python manage.py runserver 0.0.0.0:8000``. This is used to run the testing server which is accessible from ``http://localhost:8111`` (note that the port number gets changed by Vagrant)

    The rest of this tutorial will assume that you are using these aliases. If you are not using Vagrant, you should replace ``dj`` with ``python manage.py``.


With a virtual environment
==========================

TODO

Don't forget to mention ``pyvenv`` and ``virtualenv``

