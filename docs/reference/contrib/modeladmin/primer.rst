===================================
``modeladmin`` customisation primer
===================================

The ``modeladmin`` app is designed to offer you as much flexibility as possible
in how your model and its objects are represented in Wagtail's CMS. This page
aims to provide you with some background information to help you gain a better
understanding of what the app can do, and to point you in the right direction,
depending on the kind of customisations you're looking to make.

.. contents::
    :local:
    :depth: 1

---------------------------------------------------------
Wagtail's ``ModelAdmin`` class isn't the same as Django's
---------------------------------------------------------

Wagtail's ``ModelAdmin`` class is designed to be used in a similar way to
Django's class of the same name, and often uses the same attribute and method
names to achieve similar things. However, there are a few key differences:

Add & edit forms are still defined by ``panels`` and ``edit_handlers``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Wagtail, controlling which fields appear in add/edit forms for your
``Model``, and defining how they are grouped and ordered, is achieved by
adding a ``panels`` attribute, or `edit_handler` to your ``Model`` class.
This remains the same whether your model is a ``Page`` type, a snippet, or
just a standard Django ``Model``. Because of this, Wagtail's ``ModelAdmin``
class is mostly concerned with 'listing' configuration. For example,
``list_display``, ``list_filter`` and ``search_fields`` attributes are
present and support largely the same values as Django's ModelAdmin class,
while `fields`, `fieldsets`, `exclude` and other attributes you may be used
to using to configure Django's add/edit views, simply aren't supported by
Wagtail's version.

'Page type' models need to be treated differently to other models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While ``modeladmin``'s listing view and it's supported customisation
options work in exactly the same way for all types of ``Model``, when it
comes to the other management views, the treatment differs depending on
whether your ModelAdmin class is representing a page type model (that
extends ``wagtailcore.models.Page``) or not.

Pages in Wagtail have some unique properties, and require additional views,
interface elements and general treatment in order to be managed
effectively. For example, they have a tree structure that must be preserved
properly as pages are added, deleted and moved around. They also have a
revisions system, their own permission considerations, and the facility to
preview changes before saving changes. Because of this added complexity
Wagtail provides its own specific views for managing any custom page types
you  might add to your project; whether you create a ``ModelAdmin`` class
for them, or not.

In order to deliver a consistent experience for users, ``modeladmin``
simply redirects users to Wagtail's existing page management views wherever
possible. You should bare this in mind if you ever find yourself wanting to
change what happens when pages of a certain type are added, deleted,
published, or have some other action applied to them. Customising the
``CreateView`` or ``EditView`` for your a page type ``Model`` (even it just
to add an additional stylesheet or javascript), simply won't have any
effect, as those views are not used.

If you do find yourself needing to customise the add, edit or other
behaviour for a page type model, you should take a look at the following
part of the documentation: :ref:`admin_hooks`.

Wagtail's ``ModelAdmin`` class is 'modular'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unlike Django's class of the same name, wagtailadmin's ``ModelAmin`` acts
primarily as a 'controller' class. While it does have a set of attributes
and methods to enable you to configure how various components should treat
your model, it has been deliberately designed to do as little work as
possible by itself; it designates all of the real work to a set of
separate, swappable components.

The theory is: If you want to do something differently, or add some
functionality that ``modeladmin`` doesn't already have, you can create new
classes (or extend the ones provided by ``modeladmin``) and easily
configure your ``ModelAdmin`` class to use them instead of the defaults.

- Learn more about :ref:`modeladmin_overriding_views`
- Learn more about :ref:`modeladmin_overriding_helper_classes`

------------------------------------
Changing what appears in the listing
------------------------------------

You should familarise yourself with the attributes and methods supported by
the ``ModelAdmin`` class, that allow you to change what is displayed in the
``IndexView``. The following page should give you everything you need to get
going: :doc:`indexview`


.. _modeladmin_adding_css_and_js:

-----------------------------------------------
Adding additional stylesheets and/or javascript
-----------------------------------------------

The ``ModelAdmin`` class provides several attributes to enable you to easily
add additional stylesheets and javascript to the admin interface for your
model. Each atttribute simply needs to be a list of paths to the files you
want to include. If the path is for a file in your project's static directory,
Wagtail will automatically prepended paths for each path with ``STATIC_URL``,
so you don't need to repeat it each time in your list of paths.

If you'd like to add styles or scripts to the ``IndexView``, you should set the
following attributes:

-   ``index_view_extra_css`` -  Where each item is the path name of a
    pre-compiled stylesheet that you'd like to include.

-   ``index_view_extra_js`` - Where each item is the path name of a javascript
    file that you'd like to include.

If you'd like to do the same for ``CreateView`` and ``EditView``, you should
set the following attributes:

-   ``form_view_extra_css`` -  Where each item is the path name of a
    pre-compiled stylesheet that you'd like to include.

-   ``form_view_extra_js`` - Where each item is the path name of a javascript
    file that you'd like to include.

And if you're using the ``InspectView`` for your model, and want to do the same
for that view, your should set the following attributes:

-   ``inspect_view_extra_css`` -  Where each item is the path name of a
    pre-compiled stylesheet that you'd like to include.

-   ``inspect_view_extra_js`` - Where each item is the path name of a javascript
    file that you'd like to include.

.. _modeladmin_overriding_templates:

--------------------
Overriding templates
--------------------

For all modeladmin views, Wagtail looks for templates in the following folders
within your project, before resorting to the defaults:

1. ``/modeladmin/app-name/model-name/``
2. ``/modeladmin/app-name/``
3. ``/modeladmin/``

So, to override the template used by ``IndexView`` for example, you'd create a
new ``index.html`` template and put it in one of those locations.  For example,
if you wanted to do this for an ``ArticlePage`` model in a ``news`` app, you'd
add your custom template as ``modeladmin/news/article/index.html``.

For reference, ``modeladmin`` looks for templates with the following names for
each view:

-   ``'index.html'`` for ``IndexView``
-   ``'inspect.html'`` for ``InspectView``
-   ``'create.html'`` for ``CreateView``
-   ``'edit.html'`` for ``EditView``
-   ``'delete.html'`` for ``DeleteView``
-   ``'choose_parent.html'`` for ``ChooseParentView``

If for any reason you'd rather bypass this behaviour and explicitly specify a
template for a specific view, you can set either of the following attributes
on your ``ModelAdmin`` class:

- ``index_template_name`` to specify a template for ``IndexView``
- ``inspect_template_name`` to specify a template for ``InspectView``
- ``create_template_name`` to specify a template for ``CreateView``
- ``edit_template_name`` to specify a template for ``EditView``
- ``delete_template_name`` to specify a template for ``DeleteView``
- ``choose_parent_template_name`` to specify a template for ``ChooseParentView``

.. _modeladmin_overriding_views:

----------------
Overriding views
----------------

For all of the views offered by ``ModelAdmin``, the class provides an attribute
that you can override, to tell it which class you'd like to use:

- ``index_view_class``
- ``inspect_view_class``
- ``create_view_class`` (not used for 'page type' models)
- ``edit_view_class`` (not used for 'page type' models)
- ``delete_view_class`` (not used for 'page type' models)
- ``choose_parent_view_class`` (only used for 'page type' models)

For example, if you'd like to create your own view class and use it for the
``IndexView``, you would do the following:

.. code-block:: python

    from wagtail.contrib.modeladmin.views import IndexView
    from wagtail.contrib.modeladmin.options import ModelAdmin
    from .models import MyModel

    class MyCustomIndexView(IndexView):
        # New functionality and exising method overrides added here
        ...


    class MyModelAdmin(ModelAdmin):
        model = MyModel
        index_view_class = MyModelIndexView


Or, if you have no need for any of ``IndexView``'s exisiting functionality in
your view, and would rather create your own view from scratch, ``modeladmin``
will support that, too. However, it's highly recommended that you use
``modeladmin.views.WMABaseView`` as a base for your view. It'll make
integrating with your ``ModelAdmin`` class much easier, and provides a bunch of
useful attributes and methods to get you started.

.. _modeladmin_overriding_helper_classes:

-------------------------
Overriding helper classes
-------------------------

While 'view classes' are responsible for a lot of the work, there are also
a number of other tasks that ``modeladmin`` must do regularly, that need to be
handled in a consistent way, and in a number of different places. These tasks
are designated to set of simple classes (in ``modeladmin``, these are termed
'helper' classes) and can be found in ``wagtail.contrib.modeladmin.helpers``.

If you ever intend to write and use your own custom views with ``modeladmin``,
you should familiarise yourself with these helpers, as they are made available
to views via the ``modeladmin.views.WMABaseView`` view.

There are three types of 'helper class':

- **URL helpers** - That help with the consistent generation, naming and
  referencing of urls.
- **Permission helpers** - That help with ensuring only users with sufficient
  permissions can perform certain actions, or see options to perform those
  actions.
- **Button helpers** - That, with the help of the other two, helps with the
  generation of buttons for use in a number of places.

The ``ModelAdmin`` class allows you to define and use your own helper classes
by setting values on the following attributes:

.. _modeladmin_url_helper_class:

``ModelAdmin.url_helper_class``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the ``modeladmin.helpers.url.PageAdminURLHelper`` class is used 
when your model extends ``wagtailcore.models.Page``, otherwise
``modeladmin.helpers.url.AdminURLHelper`` is used.

If you find that the above helper classes don't cater for your needs, you can
easily create your own helper class, by sub-classing ``AdminURLHelper`` or
``PageAdminURLHelper`` (if your  model extend's Wagtail's ``Page`` model), and
making any neccessary additions/overrides.

Once your class is defined, set the ``url_helper_class`` attribute on
your ``ModelAdmin`` class to use your custom URLHelper, like so:

.. code-block:: python

    from wagtail.contrib.modeladmin.helpers import AdminURLHelper
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from .models import MyModel


    class MyURLHelper(AdminURLHelper):
        ...


    class MyModelAdmin(ModelAdmin):
        model = MyModel
        url_helper_class = MyURLHelper

    modeladmin_register(MyModelAdmin)


Or, if you have a more complicated use case, where simply setting that
attribute isn't possible (due to circular imports, for example) or doesn't
meet your needs, you can override the  ``get_url_helper_class`` method, like
so:

.. code-block:: python

    class MyModelAdmin(ModelAdmin):
        model = MyModel

        def get_url_helper_class(self):
            if self.some_attribute is True:
                return MyURLHelper
            return AdminURLHelper


.. _modeladmin_permission_helper_class:

``ModelAdmin.permission_helper_class``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the ``modeladmin.helpers.permission.PagePermissionHelper``
class is used when your model extends ``wagtailcore.models.Page``,
otherwise ``modeladmin.helpers.permission.PermissionHelper`` is used.

If you find that the above helper classes don't cater for your needs, you can
easily create your own helper class, by sub-classing
``PermissionHelper`` or (if your  model extend's Wagtail's ``Page`` model)
``PagePermissionHelper``, and making any neccessary additions/overrides. Once
defined, you set the ``permission_helper_class`` attribute on your
``ModelAdmin`` class to use your custom class instead of the default, like so:

.. code-block:: python

    from wagtail.contrib.modeladmin.helpers import PermissionHelper
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from .models import MyModel


    class MyPermissionHelper(PermissionHelper):
        ...


    class MyModelAdmin(ModelAdmin):
        model = MyModel
        permission_helper_class = MyPermissionHelper

    modeladmin_register(MyModelAdmin)


Or, if you have a more complicated use case, where simply setting an attribute
isn't possible or doesn't meet your needs, you can override the
``get_permission_helper_class`` method, like so:

.. code-block:: python

    class MyModelAdmin(ModelAdmin):
        model = MyModel

        def get_get_permission_helper_class(self):
            if self.some_attribute is True:
                return MyPermissionHelper
            return PermissionHelper


.. _modeladmin_button_helper_class:

``ModelAdmin.button_helper_class``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the ``modeladmin.helpers.button.PageButtonHelper`` class is used 
when your model extends ``wagtailcore.models.Page``, otherwise
``modeladmin.helpers.button.ButtonHelper`` is used.

If you wish to add or change buttons for your model's IndexView, you'll need to
create  your own button helper class, by sub-classing ``ButtonHelper`` or (if
your  model extend's Wagtail's ``Page`` model) ``PageButtonHelper``, and
make any neccessary additions/overrides. Once defined, you set the
``button_helper_class`` attribute on your ``ModelAdmin`` class to use your
custom class instead of the default, like so:

.. code-block:: python

    from wagtail.contrib.modeladmin.helpers import ButtonHelper
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from .models import MyModel


    class MyButtonHelper(ButtonHelper):
        ...


    class MyModelAdmin(ModelAdmin):
        model = MyModel
        button_helper_class = MyButtonHelper

    modeladmin_register(MyModelAdmin)


Or, if you have a more complicated use case, where simply setting an attribute
isn't possible or doesn't meet your needs, you can override the
``get_button_helper_class`` method, like so:

.. code-block:: python

    class MyModelAdmin(ModelAdmin):
        model = MyModel

        def get_button_helper_class(self):
            if self.some_attribute is True:
                return MyButtonHelper
            return ButtonHelper


.. _modeladmin_helpers_in_custom_views:

Using helpers in your custom views
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As long as you sub-class ``modeladmin.views.WMABaseView`` (or one of the more
'specific' view classes) to create your custom view, instances of each helper
should be available on instances of your class as:

- ``self.url_helper``
- ``self.permission_helper``
- ``self.button_helper``

Unlike the other two, `self.button_helper` isn't populated right away when
the view is instantiated. In order to show the right buttons for the right
users, ButtonHelper instances need to be 'request aware', so
``self.button_helper`` is only set once the view's ``dispatch()`` method has
run, which takes a ``HttpRequest`` object as an argument, from which the
current user can be identified.

