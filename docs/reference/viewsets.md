# Viewsets

Viewsets are Wagtail's mechanism for defining a group of related admin views with shared properties, as a single unit. See [Generic views](../extending/generic_views).

## ViewSet

```{eval-rst}
.. autoclass:: wagtail.admin.viewsets.base.ViewSet

   .. automethod:: on_register
   .. automethod:: get_urlpatterns
   .. automethod:: get_url_name
```

## ModelViewSet

```{eval-rst}
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

## ChooserViewSet

```{eval-rst}
.. autoclass:: wagtail.admin.viewsets.chooser.ChooserViewSet

   .. attribute:: model

   Required; the model class that this viewset will work with.

   .. autoattribute:: icon
   .. autoattribute:: choose_one_text
   .. autoattribute:: page_title
   .. autoattribute:: choose_another_text
   .. autoattribute:: edit_item_text
   .. autoattribute:: choose_view_class
   .. autoattribute:: choose_results_view_class
   .. autoattribute:: chosen_view_class
   .. autoattribute:: create_view_class
   .. autoattribute:: widget_class
   .. autoattribute:: register_widget
   .. autoattribute:: creation_form_class
   .. autoattribute:: form_fields
   .. autoattribute:: exclude_form_fields
   .. autoattribute:: create_action_label
   .. autoattribute:: create_action_clicked_label
   .. autoattribute:: creation_tab_label
   .. autoattribute:: search_tab_label
```
