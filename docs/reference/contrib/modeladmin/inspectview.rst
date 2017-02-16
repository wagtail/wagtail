======================================
Enabling & customising ``InspectView``
======================================

The ``InspectView`` is disabled by default, as it's not often useful for most
models. However, if you need a view that enables users to view more detailed
information about an instance without the option to edit it, you can easily
enable the inspect view by setting ``inspect_view_enabled=True`` on your
``ModelAdmin`` class.

When enabled, an 'Inspect' button will automatically appear for each row in
your index / listing view, linking to new page that shows values a list of
field values for that particular object.

By default, all 'concrete' fields (where the field value is stored as a column
in the database table for your model) will be shown. You can customise what
values are displayed by adding the following attributes to your ``ModelAdmin``
class:

.. contents::
    :local:
    :depth: 1

.. _modeladmin_inspect_view_fields:

------------------------------------------
``ModelAdmin.inspect_view_fields``
------------------------------------------

**Expected value:** A list or tuple, where each item is the name of a field
that you'd like ``InpectView`` to render.

A sensible value will be rendered for most field types.

If a field happens to be a ``ForeignKey`` linking to the
``wagtailimages.Image`` model, a thumbnail of that image will be rendered.

If a field happens to be a ``ForeignKey`` linking to the
``wagtaildocs.Document`` model, a link to that document will be rendered.


.. _modeladmin_inspect_view_fields_exclude:

------------------------------------------
``ModelAdmin.inspect_view_fields_exclude``
------------------------------------------

**Expected value:** A list or tuple, where each item is the name of a field
that you'd like to exclude from ``InpectView``

**Note:** If both ``inspect_view_fields`` and ``inspect_view_fields_exclude``
are set, ``inspect_view_fields_exclude`` will be ignored.

.. _modeladmin_inspect_view_extra_css:

-------------------------------------
``ModelAdmin.inspect_view_extra_css``
-------------------------------------

**Expected value**: A list of path names of additional stylesheets to be added
to the ``InspectView``

See the following part of the docs to find out more:
:ref:`modeladmin_adding_css_and_js`

.. _modeladmin_inspect_view_extra_js:

------------------------------------
``ModelAdmin.inspect_view_extra_js``
------------------------------------

**Expected value**: A list of path names of additional js files to be added
to the ``InspectView``

See the following part of the docs to find out more:
:ref:`modeladmin_adding_css_and_js`

.. _modeladmin_inspect_template_name:

---------------------------------------
``ModelAdmin.inspect_template_name``
---------------------------------------

**Expected value**: The path to a custom template to use for ``InspectView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_templates`

.. _modeladmin_inspect_view_class:

---------------------------------------
``ModelAdmin.inspect_view_class``
---------------------------------------

**Expected value**: A custom ``view`` class to replace
``modeladmin.views.InspectView``

See the following part of the docs to find out more:
:ref:`modeladmin_overriding_views`
