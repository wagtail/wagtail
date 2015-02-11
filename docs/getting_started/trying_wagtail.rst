==============
Trying Wagtail
==============


Wagtail demo
============



One line install
================


Ubuntu
------

If you have a fresh instance of Ubuntu 13.04 or later, you can install Wagtail,
along with a demonstration site containing a set of standard templates and page
types, in one step. As the root user::

  curl -O https://raw.githubusercontent.com/torchbox/wagtail/master/scripts/install/ubuntu.sh; bash ubuntu.sh

This script installs all the dependencies for a production-ready Wagtail site,
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
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
including PostgreSQL, Redis, Elasticsearch, Nginx and uwsgi. We
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
