Using Vagrant
=============

This is the easiest way to get the project running. Vagrant runs your project locally in a virtual machine so you can use PostgreSQL and Elasticsearch in development without having to install them on your host machine. If you haven't yet installed Vagrant, see: `Installing Vagrant <https://docs.vagrantup.com/v2/installation/>`_.


To setup the Vagrant box, run the following commands

 .. code-block:: bash

    vagrant up # This may take some time on first run
    vagrant ssh
    # within the ssh session
    dj createsuperuser
    djrun


If you now visit http://localhost:8000 you should see a very basic "Welcome to your new Wagtail site!" page.

You can browse the Wagtail admin interface at: http://localhost:8000/admin

You can read more about how Vagrant works at: https://docs.vagrantup.com/v2/


.. topic:: The ``dj`` and ``djrun`` aliases

    When using Vagrant, the Wagtail template provides two aliases: ``dj`` and ``djrun`` which can be used in the ``vagrant ssh`` session.

    .. glossary::

        ``dj``
        
            This is short for ``python manage.py`` so you can use it to reduce typing. For example: ``python manage.py syncdb`` becomes ``dj syncdb``.

        ``djrun``
        
            This is short for ``python manage.py runserver 0.0.0.0:8000``. This is used to run the testing server which is accessible from ``http://localhost:8000`` (note that the port number gets changed by Vagrant)
