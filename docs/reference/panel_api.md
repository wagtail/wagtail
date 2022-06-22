# Panel API

```{eval-rst}
.. module:: wagtail.admin.panels
```

## `Panel`

```{eval-rst}
.. autoclass:: Panel

   .. automethod:: bind_to_model
   .. automethod:: on_model_bound
   .. automethod:: clone
   .. automethod:: clone_kwargs
   .. automethod:: get_form_options
   .. automethod:: get_form_class
   .. automethod:: get_bound_panel
```

## `BoundPanel`

```{eval-rst}

.. autoclass:: wagtail.admin.panels.Panel.BoundPanel

   In addition to the standard template component functionality (see :ref:`creating_template_components`), this provides the following methods:

   .. automethod:: id_for_label
   .. automethod:: is_shown
```
