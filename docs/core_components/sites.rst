.. _wagtail_site_admin:

Sites
=====

Django's built-in admin interface provides the way to map a "site" (hostname or domain) to any node in the wagtail tree, using that node as the site's root. See :ref:`pages-theory`.

Access this by going to ``/django-admin/`` and then "Home › Wagtailcore › Sites." To try out a development site, add a single site with the hostname ``localhost`` at port ``8000`` and map it to one of the pieces of content you have created.

Wagtail's developers plan to move the site settings into the Wagtail admin interface.
