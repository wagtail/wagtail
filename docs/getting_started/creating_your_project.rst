=====================
Creating your project
=====================

.. contents:: Contents
    :local:


The ``wagtail start`` command
=============================

The easiest way to start a new project with wagtail is to use the ``wagtail start`` command. This command is installed into your environment when you install Wagtail (see: :doc:`installation`).

The command works the same way as ``django-admin.py startproject`` except that the produced project is pre-configured for Wagtail. It also contains some useful extras which are documented :doc:`here <getting_started/the_template>`.

To create a project, cd into a directory where you would like to create your project and run the following command:

 .. code-block:: bash

    wagtail start mysite


Running it
==========

TODO

    cd mysite
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver


Your site is now accessible at http://localhost:8000, with the admin backend available at http://localhost:8000/admin/ .


Using Vagrant
-------------

TODO


:doc:`getting_started/using_vagrant`
