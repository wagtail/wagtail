
.. _modeladmin_inspectview_customisation:

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

------------------------------------------
``ModelAdmin.inspect_view_extra_css``
------------------------------------------

**Expected value**: A list, where each item is the path name of a pre-compliled
stylesheet in your project's static files directory.

Default value: ``[]``

Description coming soon.

.. _modeladmin_inspect_view_extra_js:

------------------------------------------
``ModelAdmin.inspect_view_extra_js``
------------------------------------------

**Expected value**: A list, where each item is the path name of a pre-compliled
JS file in your project's static files directory.

Default value: ``[]``

Description coming soon.

.. _modeladmin_inspect_template_name:

------------------------------------------
``ModelAdmin.inspect_template_name``
------------------------------------------

**Expected value**: The path to a custom template.

Default value: ``''``

Description coming soon.

.. _modeladmin_inspect_view_class:

------------------------------------------
``ModelAdmin.inspect_view_class``
------------------------------------------

**Expected value**: A ``view`` class that extends 
``wagtail.contrib.modeladmin.views.WMABaseView``.

Default value: ``wagtail.contrib.modeladmin.views.InspectView``

Description coming soon.
