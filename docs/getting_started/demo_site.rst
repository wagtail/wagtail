==============
Trying Wagtail
==============


Wagtail demo
============

We provide a demo site containing a set of standard templates and page types - if you're new to Wagtail, this is the best way to try it out and familiarise yourself with how Wagtail works from the point of view of an editor.

If you're happy to use Vagrant, and you just want to set up the Wagtail demo site, or any other pre-existing Wagtail site that ships with Vagrant support, you don't need to install Wagtail at all. Install `Vagrant <http://www.vagrantup.com/>`__ and `VirtualBox <https://www.virtualbox.org/>`__, and run::

    git clone https://github.com/torchbox/wagtaildemo.git
    cd wagtaildemo
    vagrant up
    vagrant ssh


Then, within the SSH session::

    ./manage.py createsuperuser
    ./manage.py runserver 0.0.0.0:8000


This will make the demo site available on your host machine at the URL http://localhost:8000/ - you can access the Wagtail admin interface at http://localhost:8000/admin/ . Further instructions can be found at :ref:`editor_manual`.

Once you’ve experimented with the demo site and are ready to build your own site, it's time to install Wagtail on your host machine. Even if you intend to do all further Wagtail work within Vagrant, installing the Wagtail package on your host machine will provide the ``wagtail start`` command that sets up the initial file structure for your project.


One line install
================


Ubuntu
------

If you have a fresh instance of Ubuntu 13.04 or later, you can install Wagtail,
along with a demonstration site containing a set of standard templates and page
types, in one step. As the root user::

  curl -O https://raw.githubusercontent.com/torchbox/wagtail/master/scripts/install/ubuntu.sh; bash ubuntu.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uWSGI. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/ubuntu.sh>`_.


Debian
------

If you have a fresh instance of Debian 7, you can install Wagtail, along with a
demonstration site containing a set of standard templates and page types, in one
step. As the root user::

  curl -O https://raw.githubusercontent.com/torchbox/wagtail/master/scripts/install/debian.sh; bash debian.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uWSGI. We
recommend you check through the script before running it, and adapt it according
to your deployment preferences. The canonical version is at
`github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh
<https://github.com/torchbox/wagtail/blob/master/scripts/install/debian.sh>`_.


Docker
======

`@oyvindsk <https://github.com/oyvindsk>`_ has built a Dockerfile for the Wagtail demo. Simply run::

    docker run -p 8000:8000 -d oyvindsk/wagtail-demo

then access the site at http://your-ip:8000 and the admin
interface at http://your-ip:8000/admin using admin / test.

See https://index.docker.io/u/oyvindsk/wagtail-demo/ for more details.
