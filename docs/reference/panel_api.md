# Panel API

```{eval-rst}
.. module:: wagtail.admin.panels
```

This document describes the reference API for the base `Panel` and the `BoundPanel` classes that are used to render Wagtail's panels. For available panel types and how to use them, see [](editing_api).

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
   .. autoproperty:: clean_name
```

## `BoundPanel`

```{eval-rst}

.. autoclass:: wagtail.admin.panels.Panel.BoundPanel

   In addition to the standard template component functionality (see :ref:`creating_template_components`), this provides the following attributes and methods:

   .. autoattribute:: panel
   .. autoattribute:: instance
   .. autoattribute:: request
   .. autoattribute:: form
   .. autoattribute:: prefix
   .. automethod:: id_for_label
   .. automethod:: is_shown
```
