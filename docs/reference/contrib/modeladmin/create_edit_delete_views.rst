===========================================================
Customising ``CreateView``, ``EditView`` and ``DeleteView``
===========================================================

**NOTE:** ``modeladmin`` only provides 'create', 'edit' and 'delete'
functionality for non page type models (i.e. models that do not extend
``wagtailcore.models.Page``). If your model is a 'page type' model, customising
any of the following will not have any effect:

.. _modeladmin_edit_handler_customisation:

-------------------------------------------------------------
Changing which fields appear in ``CreateView`` & ``EditView``
-------------------------------------------------------------

``edit_handler`` can be used on any Django models.Model class, just like it
can be used for ``Page`` models or other models registered as ``Snippets`` in
Wagtail.

To change the way your ``MyPageModel`` is displayed in the CreateView and the
EditView, simply define an ``edit_handler`` or ``panels`` attribute on your
model class.

.. code-block:: python

    class MyPageModel(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)
        address = models.TextField()

        panels = [
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('first_name', classname='fn'),
                    FieldPanel('last_name', classname='ln'),
            ]),
            FieldPanel('address', classname='custom1',))
        ]

Or alternatively:

.. code-block:: python

    class MyPageModel(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)
        address = models.TextField()

        custom_panels = [
            MultiFieldPanel([
                FieldRowPanel([
                    FieldPanel('first_name', classname='fn'),
                    FieldPanel('last_name', classname='ln'),
            ]),
            FieldPanel('address', classname='custom1',))
        ]
        edit_handler = ObjectList(custom_panels)
        # or
        edit_handler = TabbedInterface([ObjectList(custom_panels), ObjectList(...)])

.. _modeladmin_form_view_extra_css:

-----------------------------------
``ModelAdmin.form_view_extra_css``
-----------------------------------

**Expected value**: A list of path names of additional stylesheets to be added
to ``CreateView`` and ``EditView``

See the following part of the docs to find out more:
:ref:`modeladmin_adding_css_and_js`

.. _modeladmin_form_view_extra_js:

-----------------------------------
``ModelAdmin.form_view_extra_js``
-----------------------------------

**Expected value**: A list of path names of additional js files to be added
to ``CreateView`` and ``EditView``

See the following part of the docs to find out more:
:ref:`modeladmin_adding_css_and_js`

.. _modeladmin_create_template_name:

-----------------------------------
``ModelAdmin.create_template_name``
-----------------------------------

**Expected value**: The path to a custom template to use for ``CreateView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_templates`

.. _modeladmin_create_view_class:

-----------------------------------
``ModelAdmin.create_view_class``
-----------------------------------

**Expected value**: A custom ``view`` class to replace
``modeladmin.views.CreateView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_views`

.. _modeladmin_edit_template_name:

-----------------------------------
``ModelAdmin.edit_template_name``
-----------------------------------

**Expected value**: The path to a custom template to use for ``EditView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_templates`

.. _modeladmin_edit_view_class:

-----------------------------------
``ModelAdmin.edit_view_class``
-----------------------------------

**Expected value**: A custom ``view`` class to replace
``modeladmin.views.EditView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_views`

.. _modeladmin_delete_template_name:

-----------------------------------
``ModelAdmin.delete_template_name``
-----------------------------------

**Expected value**: The path to a custom template to use for ``DeleteView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_templates`

.. _modeladmin_delete_view_class:

-----------------------------------
``ModelAdmin.delete_view_class``
-----------------------------------

**Expected value**: A custom ``view`` class to replace
``modeladmin.views.DeleteView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_views`

.. _modeladmin_form_fields_exclude:

-----------------------------------
``ModelAdmin.form_fields_exclude``
-----------------------------------

**Expected value**: A list or tuple of fields names

When using CreateView or EditView to create or update model instances, this
value will be passed to the edit form, so that any named fields will be
excluded from the form. This is particularly useful when registering ModelAdmin
classes for models from third-party apps, where defining panel configurations
on the Model itself is more complicated.
