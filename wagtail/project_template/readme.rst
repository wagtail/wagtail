{% if False %}

================
Wagtail template
================


Setup
=====

Install Django 1.6 on your host machine. (Be sure to explicitly uninstall earlier versions first, or use a virtualenv -
having earlier versions around seems to cause pre-1.4-style settings.py and urls.py files to be generated alongside the
new ones.)

To start a new project, run the following commands::

    $ django-admin.py startproject my_lovely_website --template=https://github.com/torchbox/wagtail-template/zipball/master --name=Vagrantfile --ext=html,rst
    $ cd my_lovely_website
    $ vagrant up
    $ vagrant ssh
      (then, within the SSH session:)
    $ dj createsuperuser
    $ djrun


This will make the app accessible on the host machine as http://localhost:8111/ . The codebase is located on the host
machine, exported to the VM as a shared folder; code editing and Git operations will generally be done on the host.

{% endif %}

==================
{{ project_name }}
==================
