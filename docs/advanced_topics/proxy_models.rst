.. _proxy_models:

Using proxy models with Wagtail
===============================

For Django developers, `proxy models <https://docs.djangoproject.com/en/dev/topics/db/models/#proxy-models>`_ are often a useful option to have when considering the design of models for a project. However, support for proxy models in Wagtail *is limited*, which is something you should bear in mind when considering them for you Wagtail project.

Our goal is to allow proxy models to be used freely within Wagtail, without any special considerations. The key areas for support we are working on are:


For custom ``Page`` models
--------------------------

1. Support in core Wagtail (available from Wagtail 2.5)
2. Support in ``contrib.modeladmin`` (available from Wagtail 2.5)


For other models
----------------

.. note::
    Recent changes `introduced in Django 2.2 <https://docs.djangoproject.com/en/dev/releases/2.2/#permissions-for-proxy-models>`_ should make it easier to improve support here soon. Though, it's likely that support will be limited to projects using Django 2.2 or later.

3. Support in ``contrib.modeladmin`` (not yet supported)
4. Support when registered as :ref:`snippets` (not yet supported)
