==============================
Customising the helper classes
==============================

Unlike Django's class of the same name, wagtailadmin's ``ModelAmin`` class acts
as a 'controller'. While it has a set of attributes and methods to enable you
to configure how various components should treat your model, the ``ModelAdmin``
class itself has been deliberately designed to do as little work as possible
by itsels; It designates all of the real work to a set of swappable, reuseable
components. The theory is: If you want to do something differently, you can
create new classes (or extend the ones provided by ``modeladmin``) and easily
configure your ``ModelAdmin`` class use those instead.

While 'view classes' are responsible for most of that work, there are also 
a number of other tasks that modeladmin does very often, that need to
be handled in a consistent way, and in a number of different places. These
tasks are designated to set of simple classes (in modeladmin, these are termed 
'helper classes') and can be found in ``wagtail.contrib.modeladmin.helpers``.

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

----------------------------------
``ModelAdmin.url_helper_class``
----------------------------------

Allows you to specify a different 'URL helper' class to be used, instead of the
one chosen by default.

When your ``ModelAdmin`` class is instantiated, an instance of the URL helper
class is also created, and set as an attribute on your ``ModelAdmin`` instance,
where it can easily be referenced whenever it is needed, such as creating a
set of buttons for an object, which need to link to the correct URLs in order
to perform certain actions.

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

Or, if you have a more complicated use case, where simply setting an attribute 
isn't possible or doesn't meet your needs, you can override the 
``get_url_helper_class`` method, like so:

```
class MyModelAdmin(ModelAdmin):
	model = MyModel
	
	def get_url_helper_class(self):
		if self.some_attribute is True:
			return MyURLHelper
		return AdminURLHelper
```

.. _modeladmin_permission_helper_class:

--------------------------------------
``ModelAdmin.permission_helper_class``
--------------------------------------

Allows you to specify a different 'permission helper' class to be used, instead
of the one chosen by default.

When your ``ModelAdmin`` class is instantiated, an instance of the 
``PermissionHelper`` class is also created, and set as an attribute on your
``ModelAdmin`` instance, where it can easily be referenced whenever it is
needed; such as determining whether a user is permitted to perform a specific
action, or should see a button/link enabling them to perform that action.

By default, the ``wagtail.contrib.modeladmin.helpers.PagePermissionHelper``
class is used when your model extends ``watail.wagtailcore.models.Page``,
otherwise ``wagtail.contrib.modeladmin.helpers.PermissionHelper`` is used. 

If you find that the above helper classes don't cater for your needs, you can
easily create your own helper class, by sub-classing
``PermissionHelper`` or (if your  model extend's Wagtail's ``Page`` model) 
``PagePermissionHelper``, and making any neccessary additions/overrides. Once
defined, you set the ``permission_helper_class`` attribute on your
``ModelAdmin`` class to use your custom class instead of the default, like so:

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

Or, if you have a more complicated use case, where simply setting an attribute 
isn't possible or doesn't meet your needs, you can override the 
``get_permission_helper_class`` method, like so:

```
class MyModelAdmin(ModelAdmin):
	model = MyModel
	
	def get_get_permission_helper_class(self):
		if self.some_attribute is True:
			return MyPermissionHelper
		return PermissionHelper
```

.. _modeladmin_button_helper_class:

--------------------------------------
``ModelAdmin.button_helper_class``
--------------------------------------

Allows you to specify a different 'button helper' class to be used, instead of
the one used by default.

By default, the ``wagtail.contrib.modeladmin.helpers.PageButtonHelper``
class is used when your model extends ``watail.wagtailcore.models.Page``,
otherwise ``wagtail.contrib.modeladmin.helpers.ButtonHelper`` is used. 

If you wish to add or change buttons for your model's IndexView, you'll need to
create  your own button helper class, by sub-classing ``ButtonHelper`` or (if
your  model extend's Wagtail's ``Page`` model) ``PageButtonHelper``, and
make any neccessary additions/overrides. Once defined, you set the
``button_helper_class`` attribute on your ``ModelAdmin`` class to use your
custom class instead of the default, like so:

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

Or, if you have a more complicated use case, where simply setting an attribute 
isn't possible or doesn't meet your needs, you can override the 
``get_button_helper_class`` method, like so:

```
class MyModelAdmin(ModelAdmin):
	model = MyModel
	
	def get_button_helper_class(self):
		if self.some_attribute is True:
			return MyButtonHelper
		return ButtonHelper
```

Unlike PermissionHelper and URLHelper, a ButtonHelper instance isn't created at
the time your ModelAdmin class is instantiated. In order to show the right
buttons for the right users, ButtonHelper instances need to be 'request aware',
so they're only ever instantiated by views, where a ``HttpRequest`` is
available to pass in.



