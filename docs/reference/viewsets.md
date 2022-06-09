# Viewsets

Viewsets are Wagtail's mechanism for defining a group of related admin views with shared properties, as a single unit. See [Generic views](../extending/generic_views).

```{eval-rst}

ViewSet
-------

.. autoclass:: wagtail.admin.viewsets.base.ViewSet

   .. automethod:: on_register
   .. automethod:: get_urlpatterns
   .. automethod:: get_url_name

ModelViewSet
------------

.. autoclass:: wagtail.admin.viewsets.model.ModelViewSet

   .. attribute:: model

   Required; the model class that this viewset will work with.

   .. attribute:: form_fields

   A list of model field names that should be included in the create / edit forms.

   .. attribute:: exclude_form_fields

   Used in place of ``form_fields`` to indicate that all of the model's fields except the ones listed here should appear in the create / edit forms. Either ``form_fields`` or ``exclude_form_fields`` must be supplied (unless ``get_form_class`` is being overridden).

   .. automethod:: get_form_class

   .. autoattribute:: icon
   .. autoattribute:: index_view_class
   .. autoattribute:: add_view_class
   .. autoattribute:: edit_view_class
   .. autoattribute:: delete_view_class
```
