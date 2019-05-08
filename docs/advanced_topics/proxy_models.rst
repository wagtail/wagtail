.. _proxy_models:

Using proxy models with Wagtail
===============================

For Django developers, `proxy models <https://docs.djangoproject.com/en/stable/topics/db/models/#proxy-models>`_
can be a useful option when considering the design of models for a project. However, there are
some areas in Wagtail where support for proxy models is limited. It's perfectly fine to add
references to proxy model instances (for example, linking to one from a Wagtail Page). Where
you're likely to have trouble is if you want to create, edit, or delete proxy model instances
in the Wagtail UI using the :doc:`modeldamin </reference/contrib/modeladmin/index>` app, or
by registering the model as a :doc:`Snippet </topics/snippets>`. See below for more information:


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
