Deploying Wagtail
-----------------

On your server
~~~~~~~~~~~~~~

Wagtail is straightforward to deploy on modern Linux-based distributions, but see the section on :doc:`performance </advanced_topics/performance>` for the non-Python services we recommend. If you are running Debian or Ubuntu, this installation script for our Vagrant box may be useful:

`github.com/torchbox/wagtaildemo/blob/master/etc/install/install.sh <https://github.com/torchbox/wagtaildemo/blob/master/etc/install/install.sh>`_

Our current preferences are for Nginx, Gunicorn and supervisor on Debian, but Wagtail should run with any of the combinations detailed in Django's `deployment documentation <https://docs.djangoproject.com/en/dev/howto/deployment/>`_.

On Gondor
~~~~~~~~~

`Gondor <https://gondor.io/>`_ specialise in Python hosting. They provide Redis and Elasticsearch, which are two of the services we recommend for high-performance production sites. Gondor have written a comprehensive tutorial on running your Wagtail site on their platform, at `gondor.io/blog/2014/02/14/how-run-wagtail-cms-gondor/ <https://gondor.io/blog/2014/02/14/how-run-wagtail-cms-gondor/>`_.

On other PAASs and IAASs
~~~~~~~~~~~~~~~~~~~~~~~~

We know of Wagtail sites running on `Heroku <http://spapas.github.io/2014/02/13/wagtail-tutorial/>`_, Digital Ocean and elsewhere. If you have successfully installed Wagtail on your platform or infrastructure, please :doc:`contribute </contributing/index>` your notes to this documentation!
