
.. _modeladmin_cust_reference_intro:

======================================
``ModelAdmin`` customisation reference
======================================

Below is a list of class attributes present on the ``ModelAdmin`` class, that 
can be easily overridden to customise the representation of your model within
Wagtail's CMS.

.. _modeladmin_cust_reference_helper_class_overrides:

----------------------
Helper class overrides
----------------------

``url_helper_class``
^^^^^^^^^^^^^^^^^^^^

Default value: ``None``

To ensure URLs can be generated, named and referenced consistently throughout
modeladmin's various views, a ``URLHelper`` class is used, which is simple 
class dedicated to that role. When your ``ModelAdmin`` class is instantiated,
an instance of the ``URLHelper`` class is also created, and set as an attribute
on your ``ModelAdmin`` instance, where it can easily be referenced whenever it
is needed. 

By default, the ``wagtail.contrib.modeladmin.helpers.PageAdminURLHelper`` class
is used when your model extends ``watail.wagtailcore.models.Page``, otherwise
``wagtail.contrib.modeladmin.helpers.AdminURLHelper`` is used. 

If you find that the above helper classes don't cater for your needs, you can
easily create your own helper class, by sub-classing
``AdminURLHelper`` or (if your  model extend's Wagtail's ``Page`` model) 
``PageAdminURLHelper``, and making any neccessary additions/overrides. Once
defined, you set the ``url_helper_class`` attribute on your ``ModelAdmin``
class to use your custom URLHelper, like so:

```
from wagtail.contrib.modeladmin.helpers import AdminURLHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import MyModel


class MyURLHelper(AdminURLHelper):
	...


class MyModelAdmin(ModelAdmin):
	model = MyModel
	url_helper_class = MyURLHelper

modeladmin_register(MyModelAdmin)
```

``permission_helper_class``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Default value: ``None``

To ensure that permissions are handled consistently throughout modeladmin's
various views, a ``PermissionHelper`` class is used, which is a simple class
dedicated to that role. When your ``ModelAdmin`` class is instantiated, an
instance of the ``PermissionHelper`` class is also created, and set as an
attribute on your ``ModelAdmin`` instance, where it can easily be referenced
whenever it is needed. 

By default, the ``wagtail.contrib.modeladmin.helpers.PagePermissionHelper``
class is used when your model extends ``watail.wagtailcore.models.Page``,
otherwise ``wagtail.contrib.modeladmin.helpers.PermissionHelper`` is used. 

If you find that the above helper classes don't cater for your needs, you can
easily create your own helper class, by sub-classing
``PermissionHelper`` or (if your  model extend's Wagtail's ``Page`` model) 
``PagePermissionHelper``, and making any neccessary additions/overrides. Once
defined, you set the ``permission_helper_class`` attribute on your
``ModelAdmin`` class to use your custom PermissionHelper, like so:

```
from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import MyModel


class MyPermissionHelper(PermissionHelper):
	...


class MyModelAdmin(ModelAdmin):
	model = MyModel
	permission_helper_class = MyPermissionHelper

modeladmin_register(MyModelAdmin)
```


``button_helper_class``
^^^^^^^^^^^^^^^^^^^^^^^

Default value: ``None``

In order to display buttons for each row in the IndexView for your model,
`ModelAdmin` relies on a ``ButtonHelper`` class to describe what URL, label,
and CSS class name(s) each button should have, and ensure each button is only
shown to users who have sufficient permission to perform the relevant action.

If you wish to add or change buttons for your model's IndexView, you'll need to
create  your own button helper class, by sub-classing ``ButtonHelper`` or (if
your  model extend's Wagtail's ``Page`` model) ``PageButtonHelper``, and
make any neccessary additions/overrides. Once defined, you set the
``button_helper_class`` attribute on your ``ModelAdmin`` class to use it, 
instead of the default, like so:

```
from wagtail.contrib.modeladmin.helpers import ButtonHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from .models import MyModel


class MyButtonHelper(ButtonHelper):
	...


class MyModelAdmin(ModelAdmin):
	model = MyModel
	button_helper_class = MyButtonHelper

modeladmin_register(MyModelAdmin)
```

If not set, your `ModelAdmin` class will choose the most appropriate class for
you, depeding on whether or not your model extends Wagtail's 
``wagtailcore.models.Page`` model or not.

.. _modeladmin_cust_reference_menu_item_overrides:

-----------------------
Menu item customisation
-----------------------

``menu_label``
^^^^^^^^^^^^^^

Default value: ``None``

Set this attribute to a string value to override the label used for the menu 
item that appears in Wagtail's sidebar.

If not set, the menu item will use ``verbose_name_plural`` from your model's
``Meta`` data.

``menu_icon``
^^^^^^^^^^^^^

Default value: ``None``

If you want to change the icon used to represent your Model, you can change
the ``menu_icon`` attribute on your class to use one of the other icons
available in Wagtail's CMS. The same icon will be used for the menu item in 
Wagtail's sidebar, and will also appear in the header on the list page and
other views for your Model.

If not set, the following icons will be used by default:

- ``'doc-full-inverse'`` for models that extend wagtail's `Page` model
- ``'snippet'`` for other models

If you're using a ``ModelAdminGroup`` class to group together several 
``ModelAdmin`` in their own sub-menu, and want to change
the menu item used to represent the group, you simply need to update the
``menu_icon`` attribute on your ``ModelAdminGroup`` class instead. By default
Wagtail uses ``'icon-folder-open-inverse'``.

``menu_order``
^^^^^^^^^^^^^^

Default value: ``None``

If you want to change the position of the menu item for your model (or group of
models) in Wagtail's sidebar, you do that by setting ``menu_order``. The value
should be an integer between ``1`` and ``999``. The lower the value, the higher
up the menu item will appear. 

Wagtail's 'Explorer' menu item has an order value of ``100``, so supply a value
greater than that if you wish to keep the explorer menu item at the top.
