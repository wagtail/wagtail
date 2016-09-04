
.. _modeladmin_intro:

=====================
``ModelAdmin``
=====================

The ``modeladmin`` module allows you to create customisable listing
pages for any model in your Wagtail project, and add navigation elements to the
Wagtail admin area so that you can reach them. Simply extend the ``ModelAdmin``
class, override a few attributes to suit your needs, register it with Wagtail
using an easy one-line method (you can copy and paste from the examples below),
and you're good to go.

You can use it with any Django model (it doesn’t need to extend ``Page`` or
be registered as a ``Snippet``), and it won’t interfere with any of the
existing admin functionality that Wagtail provides.

.. _modeladmin_features:

A full list of features
-----------------------

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


Supported list options
-----------------------

With the exception of bulk actions and date hierarchy, the ``ModelAdmin`` class
offers similar list functionality to Django's ``ModelAdmin`` class, providing:

- control over what values are displayed (via the ``list_display`` attribute)
- control over default ordering (via the ``ordering`` attribute)
- customisable model-specific text search (via the ``search_fields`` attribute)
- customisable filters (via the ``list_filter`` attribue)

``list_display`` supports the same fields and methods as Django's ModelAdmin
class (including ``short_description`` and ``admin_order_field`` on custom
methods), giving you lots of flexibility when it comes to output.
`Read more about list_display in the Django docs <https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display>`_.

``list_filter`` supports the same field types as Django's ModelAdmin class,
giving your users an easy way to find what they're looking for.
`Read more about list_filter in the Django docs <https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter>`_.


Customizing the layout 
----------------------

``edit_handler`` can be used on any Django models.Model classes just like it can be used on ``Page`` classes.

To change the way your ``MyPageModel`` is displayed in the CreateView and the EditView, simply define an ``edit_handler`` or ``panels`` in your model.

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
