======================================
Enabling & customising ``InspectView``
======================================

The ``InspectView`` is disabled by default, as it's not often useful for most
models. However, if you need a view that enables users to view more detailed
information about an instance without the option to edit it, you can easily
enable the inspect view by setting ``inspect_view_enabled`` on your
``ModelAdmin`` class.

When enabled, an 'Inspect' button will automatically appear for each row in
your index / listing view, linking to new page that shows values for all 
'concrete' field values (where the field value is stored in the same table
that represents the model).

You can customise what values are displayed by adding the following attributes
to your ``ModelAdmin`` class:

.. _modeladmin_inspect_view_fields:

------------------------------------------
``ModelAdmin.inspect_view_fields``
------------------------------------------

Default value: ``[]``

Description coming soon.

.. _modeladmin_inspect_view_fields:

------------------------------------------
``ModelAdmin.inspect_view_fields_exclude``
------------------------------------------

Default value: ``[]``

Description coming soon.

.. _modeladmin_inspect_view_extra_css:

-----------------------------------
``ModelAdmin.inspect_view_extra_css``
-----------------------------------

**Expected value**: A list of path names of additional stylesheets to be added
to the ``InspectView``

See the following part of the docs to find out more:
:docs:`_modeladmin_adding_css_and_js`

.. _modeladmin_inspect_view_extra_js:

-----------------------------------
``ModelAdmin.inspect_view_extra_js``
-----------------------------------

**Expected value**: A list of path names of additional js files to be added
to the ``InspectView``

See the following part of the docs to find out more:
:docs:`_modeladmin_adding_css_and_js`

.. _modeladmin_index_template_name:

---------------------------------------
``ModelAdmin.index_template_name``
---------------------------------------

**Expected value**: The path to a custom template to use for ``InspectView``

See the following part of the docs to find out more:
:docs:`modeladmin_overriding_templates`

.. _modeladmin_inspect_view_class:

---------------------------------------
``ModelAdmin.inspect_view_class``
---------------------------------------

**Expected value**: A custom ``view`` class to replace 
``modeladmin.views.InspectView``

See the following part of the docs to find out more:
:docs:`_modeladmin_overriding_views`
