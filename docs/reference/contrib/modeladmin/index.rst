=====================
``ModelAdmin``
=====================

The ``modeladmin`` module allows you to create customisable listing
pages for any model in your Wagtail project, and add navigation elements to the
Wagtail admin area so that you can access them. Simply extend the
``ModelAdmin`` class, override a few attributes to suit your needs, register
it with Wagtail using an easy one-line ``modeladmin_register`` method
(you can copy and paste from the examples below), and you're good to go.

You can use it with any Django model (it doesn’t need to extend ``Page`` or
be registered as a ``Snippet``), and it won’t interfere with any of the
existing admin functionality that Wagtail provides.

.. _modeladmin_feature_summary:

-------------------
Summary of features
-------------------

- A customisable list view, allowing you to control what values are displayed
  for each row, available options for result filtering, default ordering, and
  more.
- Access your list views from the Wagtail admin menu easily with automatically
  generated menu items, with automatic 'active item' highlighting. Control the
  label text and icons used with easy-to-change attributes on your class.
- An additional ``ModelAdminGroup`` class, that allows you to group your
  related models, and list them together in their own submenu, for a more
  logical user experience.
- Simple, robust **add** and **edit** views for your non-Page models that use
  the panel configurations defined on your model using Wagtail's edit panels.
- For Page models, the system directs to Wagtail's existing add and
  edit views, and returns you back to the correct list page, for a seamless
  experience.
- Full respect for permissions assigned to your Wagtail users and groups. Users
  will only be able to do what you want them to!
- All you need to easily hook your ``ModelAdmin`` classes into Wagtail, taking
  care of URL registration, menu changes, and registering any missing model
  permissions, so that you can assign them to Groups.
- **Built to be customisable** - While ``modeladmin`` provides a solid
  experience out of the box, you can easily use your own templates, and the
  ``ModelAdmin`` class has a large number of methods that you can override or
  extend, allowing you to customise the behaviour to a greater degree.

---------------------------------------------------
Want to know more about customising ``ModelAdmin``?
---------------------------------------------------

.. toctree::
    :maxdepth: 1

    primer
    menu_item
    indexview
    create_edit_delete_views
    inspectview
    chooseparentview

.. _modeladmin_usage:

Installation
------------

Add ``wagtail.contrib.modeladmin`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
       ...
       'wagtail.contrib.modeladmin',
    ]

How to use
----------

.. _modeladmin_example_simple:

A simple example
^^^^^^^^^^^^^^^^

You have a model in your app, and you want a listing page specifically for that
model, with a menu item added to the menu in the Wagtail admin area so that you
can get to it.

``wagtail_hooks.py`` in your app directory would look something like this:

.. code-block:: python

    from wagtail.contrib.modeladmin.options import (
        ModelAdmin, modeladmin_register)
    from .models import MyPageModel


    class MyPageModelAdmin(ModelAdmin):
        model = MyPageModel
        menu_label = 'Page Model'  # ditch this to use verbose_name_plural from model
        menu_icon = 'date'  # change as required
        menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
        add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
        exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
        list_display = ('title', 'example_field2', 'example_field3', 'live')
        list_filter = ('live', 'example_field2', 'example_field3')
        search_fields = ('title',)

    # Now you just need to register your customised ModelAdmin class with Wagtail
    modeladmin_register(MyPageModelAdmin)


.. _modeladmin_example_complex:

A more complicated example
^^^^^^^^^^^^^^^^^^^^^^^^^^

You have an app with several models that you want to show grouped together in
Wagtail's admin menu. Some of the models might extend Page, and others might
be simpler models, perhaps registered as Snippets, perhaps not. No problem!
ModelAdminGroup allows you to group them all together nicely.

``wagtail_hooks.py`` in your app directory would look something like this:

.. code-block:: python

    from wagtail.contrib.modeladmin.options import (
        ModelAdmin, ModelAdminGroup, modeladmin_register)
    from .models import (
        MyPageModel, MyOtherPageModel, MySnippetModel, SomeOtherModel)


    class MyPageModelAdmin(ModelAdmin):
        model = MyPageModel
        menu_label = 'Page Model'  # ditch this to use verbose_name_plural from model
        menu_icon = 'doc-full-inverse'  # change as required
        list_display = ('title', 'example_field2', 'example_field3', 'live')
        list_filter = ('live', 'example_field2', 'example_field3')
        search_fields = ('title',)


    class MyOtherPageModelAdmin(ModelAdmin):
        model = MyOtherPageModel
        menu_label = 'Other Page Model'  # ditch this to use verbose_name_plural from model
        menu_icon = 'doc-full-inverse'  # change as required
        list_display = ('title', 'example_field2', 'example_field3', 'live')
        list_filter = ('live', 'example_field2', 'example_field3')
        search_fields = ('title',)


    class MySnippetModelAdmin(ModelAdmin):
        model = MySnippetModel
        menu_label = 'Snippet Model'  # ditch this to use verbose_name_plural from model
        menu_icon = 'snippet'  # change as required
        list_display = ('title', 'example_field2', 'example_field3')
        list_filter = ('example_field2', 'example_field3')
        search_fields = ('title',)


    class SomeOtherModelAdmin(ModelAdmin):
        model = SomeOtherModel
        menu_label = 'Some other model'  # ditch this to use verbose_name_plural from model
        menu_icon = 'snippet'  # change as required
        list_display = ('title', 'example_field2', 'example_field3')
        list_filter = ('example_field2', 'example_field3')
        search_fields = ('title',)


    class MyModelAdminGroup(ModelAdminGroup):
        menu_label = 'My App'
        menu_icon = 'folder-open-inverse'  # change as required
        menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
        items = (MyPageModelAdmin, MyOtherPageModelAdmin, MySnippetModelAdmin, SomeOtherModelAdmin)

    # When using a ModelAdminGroup class to group several ModelAdmin classes together,
    # you only need to register the ModelAdminGroup class with Wagtail:
    modeladmin_register(MyModelAdminGroup)


.. _modeladmin_multi_registeration:

Registering multiple classes in one ``wagtail_hooks.py`` file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have an app with more than one model that you wish to manage, or even
multiple models you wish to group together with ``ModelAdminGroup`` classes,
that's possible. Just register each of your ModelAdmin classes using
``modeladmin_register``, and they'll work as expected.

.. code-block:: python

    class MyPageModelAdmin(ModelAdmin):
        model = MyPageModel
        ...

    class MyOtherPageModelAdmin(ModelAdmin):
        model = MyOtherPageModel
        ...

    class MyModelAdminGroup(ModelAdminGroup):
        label = _("Group 1")
        items = (ModelAdmin1, ModelAdmin2)
        ...

    class MyOtherModelAdminGroup(ModelAdminGroup):
        label = _("Group 2")
        items = (ModelAdmin3, ModelAdmin4)
        ...

    modeladmin_register(MyPageModelAdmin)
    modeladmin_register(MyOtherPageModelAdmin)
    modeladmin_register(MyModelAdminGroup)
    modeladmin_register(MyOtherModelAdminGroup)

