.. _proxy_models:

Using proxy models with Wagtail
===============================

For Django developers, `proxy models <https://docs.djangoproject.com/en/stable/topics/db/models/#proxy-models>`_
can be a useful option when considering the design of models for a project. However, there are
some areas in Wagtail where support for proxy models is limited. It is important to highlight that
these limitations pertain specifically to the direct management of proxy models and their related
permissions within Wagtail's admin UI - If you don't need to manage the data within Wagtail,
there's nothing to worry about! Wagtail's various edit interfaces even allow you to freely manage
an object's relationships with proxy models if they are used in ``ForeignKey``, ``ManyToManyField``
or ``ParentalManyToManyField`` fields.

The key areas where we are working to improve proxy model support are:


Proxy ``Page`` type models
--------------------------

From Wagtail 2.6, proxy page models are fully supported. You can create and manage proxy page
model instances exactly like you can for regular page models.

``Page.specific`` and ``Page.specific_class`` property methods work in exactly the same way,
and ``PageQuerySet.specific()`` will automatically use fewer database queries to retrieve
page data when proxy models are in use.


Proxy models registered with ``modeladmin``
-------------------------------------------

From Wagtail 2.6 ``modeladmin`` will work correctly for **proxy page type models**, but support for
other proxy models is still a work in progress.

While Wagtail will allow you to register other types of proxy model with ``modeladmin``, the
various CRUD views will not work correctly, and it is not possible to manage group permissions
pertaining to these models via the admin UI. In fact, registering (non page) proxy models with
``modeladmin`` can silently prevent you from managing group permissions for the 'concrete'
model, if that too has been registered.


Proxy models registered as Snippets
-----------------------------------

Wagtail will allow you to register proxy models as :doc:`Snippets </topics/snippets>`, and the various CRUD views
will work correctly for some administrators. However, it is not currently possible to manage
group permissions pertaining to these models via the admin UI. In fact, registering a proxy
model as a Snippet can silently prevent you from managing group permissions for the 'concrete'
model, if that too has been registered.
