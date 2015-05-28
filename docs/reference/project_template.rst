The project template
====================

.. code-block:: text

    mysite/
        core/
            static/
            templates/
                base.html
                404.html
                500.html
        mysite/
            settings/
                base.py
                dev.py
                production.py
        manage.py
        vagrant/
            provision.sh
        Vagrantfile
        readme.rst
        requirements.txt
        

The "core" app
----------------

Location: ``/mysite/core/``

This app is here to help get you started quicker by providing a ``HomePage`` model with migrations to create one when you first setup your app.


Default templates and static files
----------------------------------

Location: ``/mysite/core/templates/`` and ``/mysite/core/static/``

The templates directory contains ``base.html``, ``404.html`` and ``500.html``. These files are very commonly needed on Wagtail sites to they have been added into the template.

The static directory contains an empty JavaScript and SASS file. Wagtail uses ``django-compressor`` for compiling and compressing static files. For more information, see: `Django Compressor Documentation <http://django-compressor.readthedocs.org/en/latest/>`_


Vagrant configuration
---------------------

Location: ``/Vagrantfile`` and ``/vagrant/``

If you have Vagrant installed, these files let you easily setup a development environment with PostgreSQL and Elasticsearch inside a virtual machine.

If you do not want to use Vagrant, you can just delete these files.


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

            On production servers, we recommend that you only store secrets in ``local.py`` (such as API keys and passwords). This can save you headaches in the future if you are ever trying to debug why a server is behaving badly. If you are using multiple servers which need different settings then we recommend that you create a different ``production.py`` file for each one.
