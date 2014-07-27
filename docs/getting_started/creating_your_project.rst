=====================
Creating your project
=====================


The ``wagtail-project`` command
===============================

The easiest way to start a new project with wagtail is to use the ``wagtail-project`` command.


Usage:

 .. code-block:: bash

    wagtail-project project_name


This command works the same way as ``django-admin.py startproject`` except that the produced project has a few extras:

 - Pre-configured to use Wagtail
 - A requirements.txt file
 - Sphinx docs
 - Vagrant configuration
 - Separated development and production settings
 - A 'core' app with a HomePage model


.. topic:: The ``dj`` and ``djrun`` aliases

    When using Vagrant, the Wagtail template provides two aliases: ``dj`` and ``djrun``.

    ``dj`` is short for ``python manage.py`` so you can use it to reduce typing. For example: ``python manage.py syncdb`` becomes ``dj syncdb``.

    ``djrun`` is short for ``python manage.py runserver 0.0.0.0:8000``. This is used to run the testing server which is accessible from ``http://localhost:8111`` (note that the port number gets changed by Vagrant)

    The rest of this tutorial will assume that you are using these aliases. If you are not using Vagrant, you should replace ``dj`` with ``python manage.py``.


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

You can browse the Wagtail admin interface at http://localhost:8111/admin


You can read more about how Vagrant works at: https://docs.vagrantup.com/v2/


Next, you will need to create some page types so you can start adding some content and styling your website: :doc:`pages`


With a virtual environment
==========================

TODO

Don't forget to mention ``pyvenv`` and ``virtualenv``

