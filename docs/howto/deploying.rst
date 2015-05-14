Deploying Wagtail
-----------------

On your server
~~~~~~~~~~~~~~

Wagtail is straightforward to deploy on modern Linux-based distributions, but see the section on :doc:`performance </howto/performance>` for the non-Python services we recommend. If you are running Debian or Ubuntu, this installation script for our Vagrant box may be useful:

`github.com/torchbox/wagtaildemo/blob/master/etc/install/install.sh <https://github.com/torchbox/wagtaildemo/blob/master/etc/install/install.sh>`_

Our current preferences are for Nginx, Gunicorn and supervisor on Debian, but Wagtail should run with any of the combinations detailed in Django's `deployment documentation <https://docs.djangoproject.com/en/dev/howto/deployment/>`_.

On Gondor
~~~~~~~~~

`Gondor <https://gondor.io/>`_ specialise in Python hosting. They provide Redis and Elasticsearch, which are two of the services we recommend for high-performance production sites. Gondor have written a comprehensive tutorial on running your Wagtail site on their platform, at `gondor.io/blog/2014/02/14/how-run-wagtail-cms-gondor/ <https://gondor.io/blog/2014/02/14/how-run-wagtail-cms-gondor/>`_.

On other PAASs and IAASs
~~~~~~~~~~~~~~~~~~~~~~~~

We know of Wagtail sites running on `Heroku <http://spapas.github.io/2014/02/13/wagtail-tutorial/>`_, Digital Ocean and elsewhere. If you have successfully installed Wagtail on your platform or infrastructure, please :doc:`contribute </howto/contributing>` your notes to this documentation!

On Webfaction
~~~~~~~~~~~~~

Well, in web faction you need to do three aditional steps from a normal webfaction django's deploying: Install gcc>=4.6, compile and install libsass and use compress comamand in static files.

1. Install gcc>= 4.6:
You can find how do this here: `https://community.webfaction.com/questions/6921/compiling-gcc-46`. You need almost RAM 1GB, take a one hour at least in finish the installation.
Maybe you can use this script in side read all page: `https://gist.githubusercontent.com/wsfulmer/776c6fea1366fe6d142b/raw/5cd87b55e17c6048e4d4914a47e79c5e68e235d2/buildgcc.sh`

2. Install libsass:
Use `pipx.y install libsass`, is very easy.

3. Use compressor commads:
Is very important, if you don't collect the static files with compressor wagtail's admin won't have any style; compressor use libsass to compile sass files, and wagtail admin's styles are sass files.

The rest is normal django deploitment.

Is you have any doug please ask us or ask in `https://help.webfaction.com/` or `https://community.webfaction.com/questions/`.
Enjoy it
