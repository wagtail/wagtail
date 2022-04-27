# Customising `IndexView` - the listing view

For the sake of consistency, this section of the docs will refer to the listing view as `IndexView`, because that is the view class that does all the heavy lifting.

You can use the following attributes and methods on the `ModelAdmin` class to alter how your model data is treated and represented by the `IndexView`.

```{contents}
---
local:
depth: 1
---
```

(modeladmin_list_display)=

## `ModelAdmin.list_display`

**Expected value**: A list or tuple, where each item is the name of a field or single-argument callable on your model, or a similarly simple method defined on the `ModelAdmin` class itself.

Default value: `('__str__',)`

Set `list_display` to control which fields are displayed in the `IndexView` for your model.

You have three possible values that can be used in `list_display`:

-   A field of the model. For example:

    ```python
        from wagtail.contrib.modeladmin.options import ModelAdmin
        from .models import Person

        class PersonAdmin(ModelAdmin):
            model = Person
            list_display = ('first_name', 'last_name')
    ```

-   The name of a custom method on your `ModelAdmin` class, that accepts a single parameter for the model instance. For example:

    ```python
        from wagtail.contrib.modeladmin.options import ModelAdmin
        from .models import Person


        class PersonAdmin(ModelAdmin):
            model = Person
            list_display = ('upper_case_name',)

            def upper_case_name(self, obj):
                return ("%s %s" % (obj.first_name, obj.last_name)).upper()
            upper_case_name.short_description = 'Name'
    ```

-   The name of a method on your `Model` class that accepts only `self` as an argument. For example:

    ```python
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

A few special cases to note about `list_display`:

-   If the field is a `ForeignKey`, Django will display the output of `__str__()` of the related object.

-   If the string provided is a method of the model or `ModelAdmin` class, Django will HTML-escape the output by default. To escape user input and allow your own unescaped tags, use `format_html()`. For example:

    ```python
        from django.db import models
        from django.utils.html import format_html
        from wagtail.contrib.modeladmin.options import ModelAdmin

        class Person(models.Model):
            first_name = models.CharField(max_length=50)
            last_name = models.CharField(max_length=50)
            color_code = models.CharField(max_length=6)

            def styled_name(self):
                return format_html(
                    '<span style="color: #{};">{} {}</span>',
                    self.color_code,
                    self.first_name,
                    self.last_name,
                )


        class PersonAdmin(ModelAdmin):
            model = Person
            list_display = ('first_name', 'last_name', 'styled_name')
    ```

-   If the value of a field is `None`, an empty string, or an iterable without elements, Wagtail will display a dash (-) for that column. You can override this by setting `empty_value_display` on your `ModelAdmin` class. For example:

    ```python
        from wagtail.contrib.modeladmin.options import ModelAdmin

        class PersonAdmin(ModelAdmin):
            empty_value_display = 'N/A'
            ...
    ```

    Or, if you'd like to change the value used depending on the field, you can override `ModelAdmin`'s `get_empty_value_display()` method, like so:

    ```python
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
                return super().get_empty_value_display(field_name)
    ```

    The `__str__()` method is just as valid in `list_display` as any other model method, so it’s perfectly OK to do this:

    ```python
        list_display = ('__str__', 'some_other_field')
    ```

    By default, the ability to sort results by an item in `list_display` is only offered when it's a field that has an actual database value (because sorting is done at the database level). However, if the output of the method is representative of a database field, you can indicate this fact by setting the `admin_order_field` attribute on that method, like so:

    ```python
        from django.db import models
        from django.utils.html import format_html
        from wagtail.contrib.modeladmin.options import ModelAdmin

        class Person(models.Model):
            first_name = models.CharField(max_length=50)
            last_name = models.CharField(max_length=50)
            color_code = models.CharField(max_length=6)

            def styled_first_name(self):
                return format_html(
                    '<span style="color: #{};">{}</span>',
                    self.color_code,
                    self.first_name,
                )
            styled_first_name.admin_order_field = 'first_name'


        class PersonAdmin(ModelAdmin):
            model = Person
            list_display = ('styled_first_name', 'last_name')
    ```

    The above will tell Wagtail to order by the `first_name` field when trying to sort by `styled_first_name` in the index view.

    The above will tell Wagtail to order by the `first_name` field when
    trying to sort by `styled_first_name` in the index view.

    To indicate descending order with `admin_order_field` you can use a
    hyphen prefix on the field name. Using the above example, this would look
    like:

    .. code-block:: python

        styled_first_name.admin_order_field = '-first_name'

    `admin_order_field` supports query lookups to sort by values on related models, too. This example includes an “author first name” column in the list display and allows sorting it by first name:

    ```python
        from django.db import models


        class Blog(models.Model):
            title = models.CharField(max_length=255)
            author = models.ForeignKey(Person, on_delete=models.CASCADE)

            def author_first_name(self, obj):
                return obj.author.first_name

            author_first_name.admin_order_field = 'author__first_name'
    ```

-   Elements of `list_display` can also be properties. Please note however, that due to the way properties work in Python, setting `short_description` on a property is only possible when using the `property()` function and **not** with the `@property` decorator.

    For example:

    ```python
        from django.db import models
        from wagtail.contrib.modeladmin.options import ModelAdmin

        class Person(models.Model):
            first_name = models.CharField(max_length=50)
            last_name = models.CharField(max_length=50)

            def full_name_property(self):
                return self.first_name + ' ' + self.last_name
            full_name_property.short_description = "Full name of the person"

            full_name = property(full_name_property)


        class PersonAdmin(ModelAdmin):
            list_display = ('full_name',)
    ```

(modeladmin_list_export)=

## `ModelAdmin.list_export`

**Expected value**: A list or tuple, where each item is the name of a field or single-argument callable on your model, or a similarly simple method defined on the `ModelAdmin` class itself.

Set `list_export` to set the fields you wish to be exported as columns when downloading a spreadsheet version of your index_view

```python
    class PersonAdmin(ModelAdmin):
        list_export = ('is_staff', 'company')
```

(modeladmin_list_filter)=

## `ModelAdmin.list_filter`

**Expected value**: A list or tuple, where each item is the name of model field of type `BooleanField`, `CharField`, `DateField`, `DateTimeField`, `IntegerField` or `ForeignKey`.

Set `list_filter` to activate filters in the right sidebar of the list page for your model. For example:

```python
    class PersonAdmin(ModelAdmin):
        list_filter = ('is_staff', 'company')
```

(modeladmin_export_filename)=

## `ModelAdmin.export_filename`

**Expected value**: A string specifying the filename of an exported spreadsheet, without file extensions.

```python
    class PersonAdmin(ModelAdmin):
        export_filename = 'people_spreadsheet'
```

(modeladmin_search_fields)=

## `ModelAdmin.search_fields`

**Expected value**: A list or tuple, where each item is the name of a model field of type `CharField`, `TextField`, `RichTextField` or `StreamField`.

Set `search_fields` to enable a search box at the top of the index page for your model. You should add names of any fields on the model that should be searched whenever somebody submits a search query using the search box.

Searching is handled via Django's QuerySet API by default, see [](modeladmin_search_handler_class) about changing this behaviour. This means by default it will work for all models, whatever search backend your project is using, and without any additional setup or configuration.

(modeladmin_search_handler_class)=

## `ModelAdmin.search_handler_class`

**Expected value**: A subclass of `wagtail.contrib.modeladmin.helpers.search.BaseSearchHandler`

The default value is `DjangoORMSearchHandler`, which uses the Django ORM to perform lookups on the fields specified by `search_fields`.

If you would prefer to use the built-in Wagtail search backend to search your models, you can use the `WagtailBackendSearchHandler` class instead. For example:

```python
    from wagtail.contrib.modeladmin.helpers import WagtailBackendSearchHandler

    from .models import Person

    class PersonAdmin(ModelAdmin):
        model = Person
        search_handler_class = WagtailBackendSearchHandler
```

### Extra considerations when using `WagtailBackendSearchHandler`

#### `ModelAdmin.search_fields` is used differently

The value of `search_fields` is passed to the underlying search backend to limit the fields used when matching. Each item in the list must be indexed on your model using [](wagtailsearch_index_searchfield).

To allow matching on **any** indexed field, set the `search_fields` attribute on your `ModelAdmin` class to `None`, or remove it completely.

#### Indexing extra fields using `index.FilterField`

The underlying search backend must be able to interpret all of the fields and relationships used in the queryset created by `IndexView`, including those used in `prefetch()` or `select_related()` queryset methods, or used in `list_display`, `list_filter` or `ordering`.

Be sure to test things thoroughly in a development environment (ideally using the same search backend as you use in production). Wagtail will raise an `IndexError` if the backend encounters something it does not understand, and will tell you what you need to change.

(modeladmin_extra_search_kwargs)=

## `ModelAdmin.extra_search_kwargs`

**Expected value**: A dictionary of keyword arguments that will be passed on to the `search()` method of `search_handler_class`.

For example, to override the `WagtailBackendSearchHandler` default operator you could do the following:

```python
    from wagtail.contrib.modeladmin.helpers import WagtailBackendSearchHandler
    from wagtail.search.utils import OR

    from .models import IndexedModel

    class DemoAdmin(ModelAdmin):
        model = IndexedModel
        search_handler_class = WagtailBackendSearchHandler
        extra_search_kwargs = {'operator': OR}
```

(modeladmin_ordering)=

## `ModelAdmin.ordering`

**Expected value**: A list or tuple in the same format as a model’s [ordering](django.db.models.Options.ordering) parameter.

Set `ordering` to specify the default ordering of objects when listed by IndexView. If not provided, the model’s default ordering will be respected.

If you need to specify a dynamic order (for example, depending on user or language) you can override the `get_ordering()` method instead.

(modeladmin_list_per_page)=

## `ModelAdmin.list_per_page`

**Expected value**: A positive integer

Set `list_per_page` to control how many items appear on each paginated page of the index view. By default, this is set to `100`.

(modeladmin_get_queryset)=

## `ModelAdmin.get_queryset()`

**Must return**: A QuerySet

The `get_queryset` method returns the 'base' QuerySet for your model, to which any filters and search queries are applied. By default, the `all()` method of your model's default manager is used. But, if for any reason you only want a certain sub-set of objects to appear in the IndexView listing, overriding the `get_queryset` method on your `ModelAdmin` class can help you with that. The method takes an `HttpRequest` object as a parameter, so
limiting objects by the current logged-in user is possible.

For example:

```python
    from django.db import models
    from wagtail.contrib.modeladmin.options import ModelAdmin

    class Person(models.Model):
        first_name = models.CharField(max_length=50)
        last_name = models.CharField(max_length=50)
        managed_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)


    class PersonAdmin(ModelAdmin):
        model = Person
        list_display = ('first_name', 'last_name')

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            # Only show people managed by the current user
            return qs.filter(managed_by=request.user)
```

(modeladmin_get_extra_attrs_for_row)=

## `ModelAdmin.get_extra_attrs_for_row()`

**Must return**: A dictionary

The `get_extra_attrs_for_row` method allows you to add html attributes to the opening `<tr>` tag for each result, in addition to the `data-object_pk` and `class` attributes already added by the `result_row_display` template tag.

If you want to add additional CSS classes, simply provide those class names as a string value using the `'class'` key, and the `odd`/`even` will be appended to your custom class names when rendering.

For example, if you wanted to add some additional class names based on field values, you could do something like:

```python
    from decimal import Decimal
    from django.db import models
    from wagtail.contrib.modeladmin.options import ModelAdmin

    class BankAccount(models.Model):
        name = models.CharField(max_length=50)
        account_number = models.CharField(max_length=50)
        balance = models.DecimalField(max_digits=5, num_places=2)


    class BankAccountAdmin(ModelAdmin):
        list_display = ('name', 'account_number', 'balance')

        def get_extra_attrs_for_row(self, obj, context):
            if obj.balance < Decimal('0.00'):
                classname = 'balance-negative'
            else:
                classname = 'balance-positive'
            return {
                'class': classname,
            }
```

(modeladmin_get_extra_class_names_for_field_col)=

## `ModelAdmin.get_extra_class_names_for_field_col()`

**Must return**: A list

The `get_extra_class_names_for_field_col` method allows you to add additional CSS class names to any of the columns defined by `list_display` for your model. The method takes two parameters:

-   `obj`: the object being represented by the current row
-   `field_name`: the item from `list_display` being represented by the current column

For example, if you'd like to apply some conditional formatting to a cell
depending on the row's value, you could do something like:

```python
    from decimal import Decimal
    from django.db import models
    from wagtail.contrib.modeladmin.options import ModelAdmin

    class BankAccount(models.Model):
        name = models.CharField(max_length=50)
        account_number = models.CharField(max_length=50)
        balance = models.DecimalField(max_digits=5, num_places=2)


    class BankAccountAdmin(ModelAdmin):
        list_display = ('name', 'account_number', 'balance')

        def get_extra_class_names_for_field_col(self, obj, field_name):
            if field_name == 'balance':
                if obj.balance <= Decimal('-100.00'):
                    return ['brand-danger']
                elif obj.balance <= Decimal('-0.00'):
                    return ['brand-warning']
                elif obj.balance <= Decimal('50.00'):
                    return ['brand-info']
                else:
                    return ['brand-success']
            return []
```

(modeladmin_get_extra_attrs_for_field_col)=

## `ModelAdmin.get_extra_attrs_for_field_col()`

**Must return**: A dictionary

The `get_extra_attrs_for_field_col` method allows you to add additional HTML attributes to any of the columns defined in `list_display`. Like the `get_extra_class_names_for_field_col` method above, this method takes two parameters:

-   `obj`: the object being represented by the current row
-   `field_name`: the item from `list_display` being represented by the current column

For example, you might like to add some tooltip text to a certain column, to
help give the value more context:

```python
    from django.db import models
    from wagtail.contrib.modeladmin.options import ModelAdmin


    class Person(models.Model):
        name = models.CharField(max_length=100)
        likes_cat_gifs = models.NullBooleanField()


    class PersonAdmin(ModelAdmin):
        model = Person
        list_display = ('name', 'likes_cat_gifs')

        def get_extra_attrs_for_field_col(self, obj, field_name=None):
            attrs = super().get_extra_attrs_for_field_col(obj, field_name)
            if field_name == 'likes_cat_gifs' and obj.likes_cat_gifs is None:
                attrs.update({
                    'title': (
                        'The person was shown several cat gifs, but failed to '
                        'indicate a preference.'
                    ),
                })
            return attrs
```

Or you might like to add one or more data attributes to help implement some kind of interactivity using JavaScript:

```python
    from django.db import models
    from wagtail.contrib.modeladmin.options import ModelAdmin


    class Event(models.Model):
        title = models.CharField(max_length=255)
        start_date = models.DateField()
        end_date = models.DateField()
        start_time = models.TimeField()
        end_time = models.TimeField()


    class EventAdmin(ModelAdmin):
        model = Event
        list_display = ('title', 'start_date', 'end_date')

        def get_extra_attrs_for_field_col(self, obj, field_name=None):
            attrs = super().get_extra_attrs_for_field_col(obj, field_name)
            if field_name == 'start_date':
                # Add the start time as data to the 'start_date' cell
                attrs.update({ 'data-time': obj.start_time.strftime('%H:%M') })
            elif field_name == 'end_date':
                # Add the end time as data to the 'end_date' cell
                attrs.update({ 'data-time': obj.end_time.strftime('%H:%M') })
            return attrs
```

(modeladmin_thumbnailmixin)=

## `wagtail.contrib.modeladmin.mixins.ThumbnailMixin`

If you're using `wagtailimages.Image` to define an image for each item in your model, `ThumbnailMixin` can help you add thumbnail versions of that image to each row in `IndexView`. To use it, simply extend `ThumbnailMixin`
as well as `ModelAdmin` when defining your `ModelAdmin` class, and change a few attributes to change the thumbnail to your liking, like so:

```python
    from django.db import models
    from wagtail.contrib.modeladmin.mixins import ThumbnailMixin
    from wagtail.contrib.modeladmin.options import ModelAdmin

    class Person(models.Model):
        name = models.CharField(max_length=255)
        avatar = models.ForeignKey('wagtailimages.Image', on_delete=models.SET_NULL, null=True)
        likes_cat_gifs = models.NullBooleanField()

    class PersonAdmin(ThumbnailMixin, ModelAdmin):

        # Add 'admin_thumb' to list_display, where you want the thumbnail to appear
        list_display = ('admin_thumb', 'name', 'likes_cat_gifs')

        # Optionally tell IndexView to add buttons to a different column (if the
        # first column contains the thumbnail, the buttons are likely better off
        # displayed elsewhere)
        list_display_add_buttons = 'name'

        """
        Set 'thumb_image_field_name' to the name of the ForeignKey field that
        links to 'wagtailimages.Image'
        """
        thumb_image_field_name = 'avatar'

        # Optionally override the filter spec used to create each thumb
        thumb_image_filter_spec = 'fill-100x100' # this is the default

        # Optionally override the 'width' attribute value added to each `<img>` tag
        thumb_image_width = 50 # this is the default

        # Optionally override the class name added to each `<img>` tag
        thumb_classname = 'admin-thumb' # this is the default

        # Optionally override the text that appears in the column header
        thumb_col_header_text = 'image' # this is the default

        # Optionally specify a fallback image to be used when the object doesn't
        # have an image set, or the image has been deleted. It can an image from
        # your static files folder, or an external URL.
        thumb_default = 'https://lorempixel.com/100/100'
```

(modeladmin_list_display_add_buttons)=

## `ModelAdmin.list_display_add_buttons`

**Expected value**: A string matching one of the items in `list_display`.

If for any reason you'd like to change which column the action buttons appear in for each row, you can specify a different column using `list_display_add_buttons` on your `ModelAdmin` class. The value must match one of the items your class's `list_display` attribute. By default, buttons are added to the first column of each row.

See the `ThumbnailMixin` example above to see how `list_display_add_buttons` can be used.

(modeladmin_index_view_extra_css)=

## `ModelAdmin.index_view_extra_css`

**Expected value**: A list of path names of additional stylesheets to be added to the `IndexView`

See the following part of the docs to find out more: [](modeladmin_adding_css_and_js)

(modeladmin_index_view_extra_js)=

## `ModelAdmin.index_view_extra_js`

**Expected value**: A list of path names of additional js files to be added to the `IndexView`

See the following part of the docs to find out more: [](modeladmin_adding_css_and_js)

(modeladmin_index_template_name)=

## `ModelAdmin.index_template_name`

**Expected value**: The path to a custom template to use for `IndexView`

See the following part of the docs to find out more: [](modeladmin_overriding_templates)

(modeladmin_index_view_class)=

## `ModelAdmin.index_view_class`

**Expected value**: A custom `view` class to replace `modeladmin.views.IndexView`

See the following part of the docs to find out more: [](modeladmin_overriding_views)
