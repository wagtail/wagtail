============================================
Customising ``IndexView`` - the listing view
============================================

For the sake of consistency, this section of the docs will refer to the list
view as ``IndexView``, because that is the view class that does all the heavy
lifting.

You can use the following attributes and methods on the ``ModelAdmin`` class to
alter how your model data is treated and represented by the ``IndexView``.

.. _modeladmin_list_display:

---------------------------
``ModelAdmin.list_display``
---------------------------

**Expected value**: A list or tuple, where each item is the name of a field or
single-argument callable on your model, or a similarly simple method defined
on the ``ModelAdmin`` class itself.

Default value: ``('__str__',)``

Set ``list_display`` to control which fields are displayed on the list page 
for your model.

Example

```
list_display = ('first_name', 'last_name')	
```

You have three possible values that can be used in list_display:

-	A field of the model. For example: 

	```
	from wagtail.contrib.modeladmin.options import ModelAdmin
	from .models import Person

  	class PersonAdmin(ModelAdmin):
  		model = Person
      	list_display = ('first_name', 'last_name')
	```

-	The name of a custom method on your ``ModelAdmin`` class, that accepts a
	single parameter for the model instance. For example:

	```
	from wagtail.contrib.modeladmin.options import ModelAdmin
	from .models import Person


	class PersonAdmin(ModelAdmin):
		model = Person
    	list_display = ('upper_case_name',)

    	def upper_case_name(self, obj):
        	return ("%s %s" % (obj.first_name, obj.last_name)).upper()
    	upper_case_name.short_description = 'Name'
	```

- 	The name of a method on your ``Model`` class that accepts only ``self`` as
	an argument. For example:

	```
	from django.db import models
	from wagtail.contrib.modeladmin.options import ModelAdmin

	class Person(models.Model):
    	name = models.CharField(max_length=50)
    	birthday = models.DateField()

    	def decade_born_in(self):
        	return self.birthday.strftime('%Y')[:3] + "0's"
    	decade_born_in.short_description = 'Birth decade'


	class PersonAdmin(ModelAdmin):
		model = Person
    	list_display = ('name', 'decade_born_in')
	```

A few special cases to note about ``list_display``:

-	If the field is a ``ForeignKey``, Django will display the output of
	``__str__()`` (``__unicode__()`` on Python 2) of the related object.

-	If the string provided is a method of the model or ``ModelAdmin`` class,
	Django will HTML-escape the output by default. To escape user input and
	allow your own unescaped tags, use ``format_html()``. For example:

	```
	from django.db import models
	from django.utils.html import format_html
	from wagtail.contrib.modeladmin.options import ModelAdmin

	class Person(models.Model):
    	first_name = models.CharField(max_length=50)
    	last_name = models.CharField(max_length=50)
    	color_code = models.CharField(max_length=6)

    	def colored_name(self):
        	return format_html(
            	'<span style="color: #{};">{} {}</span>',
           		self.color_code,
            	self.first_name,
            	self.last_name,
        	)


	class PersonAdmin(ModelAdmin):
		model = Person
    	list_display = ('first_name', 'last_name', 'colored_name')
	```

-	If the value of a field is ``None``, an empty string, or an iterable
	without elements, Wagtail will display a dash (-) for that column. You can
	override this by setting ``empty_value_display`` on your ``ModelAdmin``
	class. For example:

	```
	from wagtail.contrib.modeladmin.options import ModelAdmin

	class PersonAdmin(ModelAdmin):
		empty_value_display = 'N/A'
		...
	```

	Or, if you'd like to change the value used depending on the field, you can
	override ``ModelAdmin``'s ``get_empty_value_display()`` method, like so:

	```
	from django.db import models
	from wagtail.contrib.modeladmin.options import ModelAdmin


	class Person(models.Model):
    	name = models.CharField(max_length=100)
    	nickname = models.CharField(blank=True, max_length=100)
    	likes_cat_gifs = models.NullBooleanField()


	class PersonAdmin(ModelAdmin):
		model = Person
		list_display = ('name', 'nickname', 'likes_cat_gifs')

		def get_empty_value_display(self, field_name=None):
	        if field_name == 'nickname':
	        	return 'None given'
	        if field_name == 'likes_cat_gifs':
	        	return 'Unanswered'
	        return super(self, PersonAdmin).get_empty_value_display(field_name)
	```

	The ``__str__()`` (``__unicode__()`` on Python 2) method is just as valid
	in ``list_display`` as any other model method, so it’s perfectly OK to do
	this:

	```
	list_display = ('__str__', 'some_other_field')
	```

	By default, the ability to sort results by an item in ``list_display`` is
	only offered when it's a field that has an actual database value (because 
	sorting is done at the database level). However, if the output of the
	method is representative of a database field, you can indicate this fact by 
	setting the ``admin_order_field`` attribute on that method, like so:

	```
	from django.db import models
	from django.utils.html import format_html
	from wagtail.contrib.modeladmin.options import ModelAdmin

	class Person(models.Model):
    	first_name = models.CharField(max_length=50)
    	last_name = models.CharField(max_length=50)
    	color_code = models.CharField(max_length=6)

    	def colored_first_name(self):
        	return format_html(
            	'<span style="color: #{};">{}</span>',
           		self.color_code,
            	self.first_name,
        	)
        colored_first_name.admin_order_field = 'first_name'


	class PersonAdmin(ModelAdmin):
		model = Person
    	list_display = ('first_name', 'colored_name')
	```

	The above will tell Wagtail to order by the ``first_name`` field when
	trying to sort by ``colored_first_name`` in the index view.

	To indicate descending order with ``admin_order_field`` you can use a
	hyphen prefix on the field name. Using the above example, this would look
	like:

	```
	colored_first_name.admin_order_field = '-first_name'
	```

	``admin_order_field`` supports query lookups to sort by values on related
	models, too. This example includes an “author first name” column in the
	list display and allows sorting it by first name:

	```
	from django.db import models
	
	
	class Blog(models.Model):
    	title = models.CharField(max_length=255)
    	author = models.ForeignKey(Person, on_delete=models.CASCADE)

    	def author_first_name(self, obj):
        	return obj.author.first_name

        author_first_name.admin_order_field = 'author__first_name'
	```

- 	Elements of ``list_display`` can also be properties. Please note however,
	that due to the way properties work in Python, setting 
	``short_description`` on a property is only possible when using the 
	``property()`` function and **not** with the ``@property`` decorator.

	For example:

	```
	from django.db import models
	from wagtail.contrib.modeladmin.options import ModelAdmin

	class Person(models.Model):
    	first_name = models.CharField(max_length=50)
    	last_name = models.CharField(max_length=50)

    	def full_name_property(self):
        	return self.first_name + ' ' + self.last_name
    	full_name_property.short_description = "Full name of the person"

    	full_name = property(full_name_property)

	
	class PersonAdmin(admin.ModelAdmin):
    	list_display = ('full_name',)
	```

.. _modeladmin_list_filter:

---------------------------
``ModelAdmin.list_filter``
---------------------------

**Expected value**: A list or tuple, where each item is the name of model field
of type ``BooleanField``, ``CharField``, ``DateField``, ``DateTimeField``, 
``IntegerField`` or ``ForeignKey``.

Set ``list_filter`` to activate filters in the right sidebar of the list page
for your model. For example:

```
class PersonAdmin(ModelAdmin):
    list_filter = ('is_staff', 'company')
```

.. _modeladmin_search_fields:

---------------------------
``ModelAdmin.search_fields``
---------------------------

**Expected value**: A list or tuple, where each item is the name of a model field
of type ``CharField``, ``TextField``, ``RichTextField`` or ``StreamField``.

Set ``search_fields`` to enable a search box at the top of the index page
for your model. You should add names of any fields on the model that should 
be searched whenever somebody submits a search query using the search box.

Searching is all handled via Django's queryset API, rather than using the
Wagtail's search backend. This means it will work for all models, whatever 
search back-end your project is using, and without any further setup needed.

.. _modeladmin_ordering:

---------------------------
``ModelAdmin.ordering``
---------------------------

**Expected value**: A list or tuple in the same format as a model’s [``ordering``](
https://docs.djangoproject.com/en/1.9/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_display) parameter.

Set ``ordering`` to specify the default ordering of objects when listed in the
index view.  If not provided, the model’s default ordering will be respected.

If you need to specify a dynamic order (for example, depending on user or
language) you can override the ``get_ordering()`` method instead.


.. _modeladmin_list_per_page:

---------------------------
``ModelAdmin.list_per_page``
---------------------------

**Expected value**: A positive integer

Set ``list_per_page`` to control how many items appear on each paginated page
of the index view. By default, this is set to ``100``.

.. _modeladmin_get_queryset:

-----------------------------
``ModelAdmin.get_queryset()``
-----------------------------

Description coming soon.

.. _modeladmin_get_extra_class_names_for_field_col:

----------------------------------------------------
``ModelAdmin.get_extra_class_names_for_field_col()``
----------------------------------------------------

Description coming soon.

.. _modeladmin_get_extra_attrs_for_field_col:

----------------------------------------------------
``ModelAdmin.get_extra_attrs_for_field_col()``
----------------------------------------------------

Description coming soon.


.. _modeladmin_index_view_extra_css:

-----------------------------------
``ModelAdmin.index_view_extra_css``
-----------------------------------

**Expected value**: A list, where each item is the path name of a pre-compliled
stylesheet in your project's static files directory.

Description coming soon.

.. _modeladmin_index_view_extra_js:

-----------------------------------
``ModelAdmin.index_view_extra_js``
-----------------------------------

**Expected value**: A list, where each item is the path name of a pre-compliled
JS file in your project's static files directory.

Description coming soon.

.. _modeladmin_list_display_add_buttons:

---------------------------------------
``ModelAdmin.list_display_add_buttons``
---------------------------------------

**Expected value**: A string matching one of the items in ``list_display``.

Default value: ``None``

Description coming soon.

.. _modeladmin_index_template_name:

---------------------------------------
``ModelAdmin.index_template_name``
---------------------------------------

**Expected value**: The path to a custom template.

Default value: ``''``

Description coming soon.

.. _modeladmin_index_view_class:

---------------------------------------
``ModelAdmin.index_view_class``
---------------------------------------

**Expected value**: A ``view`` class that extends 
``wagtail.contrib.modeladmin.views.WMABaseView``.

Default value: ``wagtail.contrib.modeladmin.views.IndexView``

Description coming soon.
