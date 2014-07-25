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

