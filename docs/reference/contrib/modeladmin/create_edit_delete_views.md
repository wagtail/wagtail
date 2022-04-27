# Customising `CreateView`, `EditView` and `DeleteView`

```{note}
**NOTE:** `modeladmin` only provides 'create', 'edit' and 'delete' functionality for non page type models (i.e. models that do not extend `wagtailcore.models.Page`). If your model is a 'page type' model, customising any of the following will not have any effect:
```

(modeladmin_edit_handler_customisation)=

# Changing which fields appear in `CreateView` & `EditView`

`edit_handler` can be used on any Django models.Model class, just like it can be used for `Page` models or other models registered as `Snippets` in Wagtail.

To change the way your `MyPageModel` is displayed in the CreateView and the EditView, simply define an `edit_handler` or `panels` attribute on your model class.

```python
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
                FieldPanel('address', classname='custom1',)
            ])
        ]
```

Or alternatively:

```python
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
                FieldPanel('address', classname='custom1',)
            ])
        ]
        edit_handler = ObjectList(custom_panels)
        # or
        edit_handler = TabbedInterface([
            ObjectList(custom_panels, heading='First Tab'),
            ObjectList(...)
        ])
```

`edit_handler` and `panels` can alternatively be defined on a `ModelAdmin` definition. This feature is especially useful for use cases where you have to work with models that are 'out of reach' (due to being part of a third-party package, for example).

```python
    class BookAdmin(ModelAdmin):
        model = Book

        panels = [
            FieldPanel('title'),
            FieldPanel('author'),
        ]
```

Or alternatively:

```python
    class BookAdmin(ModelAdmin):
        model = Book

        custom_panels = [
            FieldPanel('title'),
            FieldPanel('author'),
        ]
        edit_handler = ObjectList(custom_panels)
```

(modeladmin_form_view_extra_css)=

## `ModelAdmin.form_view_extra_css`

**Expected value**: A list of path names of additional stylesheets to be added to `CreateView` and `EditView`

See the following part of the docs to find out more: [](modeladmin_adding_css_and_js)

(modeladmin_form_view_extra_js)=

## `ModelAdmin.form_view_extra_js`

**Expected value**: A list of path names of additional js files to be added to `CreateView` and `EditView`

See the following part of the docs to find out more: [](modeladmin_adding_css_and_js)

(modeladmin_create_template_name)=

## `ModelAdmin.create_template_name`

**Expected value**: The path to a custom template to use for `CreateView`

See the following part of the docs to find out more: [](modeladmin_overriding_templates)

(modeladmin_create_view_class)=

## `ModelAdmin.create_view_class`

**Expected value**: A custom `view` class to replace `modeladmin.views.CreateView`

See the following part of the docs to find out more: [](modeladmin_overriding_views)

(modeladmin_edit_template_name)=

## `ModelAdmin.edit_template_name`

**Expected value**: The path to a custom template to use for `EditView`

See the following part of the docs to find out more: [](modeladmin_overriding_templates)

(modeladmin_edit_view_class)=

## `ModelAdmin.edit_view_class`

**Expected value**: A custom `view` class to replace `modeladmin.views.EditView`

See the following part of the docs to find out more: [](modeladmin_overriding_views)

(modeladmin_delete_template_name)=

## `ModelAdmin.delete_template_name`

**Expected value**: The path to a custom template to use for `DeleteView`

See the following part of the docs to find out more: [](modeladmin_overriding_templates)

(modeladmin_delete_view_class)=

## `ModelAdmin.delete_view_class`

**Expected value**: A custom `view` class to replace `modeladmin.views.DeleteView`

See the following part of the docs to find out more: [](modeladmin_overriding_views)

(modeladmin_form_fields_exclude)=

## `ModelAdmin.form_fields_exclude`

**Expected value**: A list or tuple of fields names

When using CreateView or EditView to create or update model instances, this value will be passed to the edit form, so that any named fields will be excluded from the form. This is particularly useful when registering ModelAdmin classes for models from third-party apps, where defining panel configurations on the Model itself is more complicated.

(modeladmin_prepopulated_fields)=

## `ModelAdmin.prepopulated_fields`

**Expected value**: A dict mapping prepopulated fields to a tuple of fields to prepopulate from

When using CreateView or EditView to create or update model instances, the fields corresponding to the keys in the dict are prepopulated using the fields in the corresponding tuple. The main use for this functionality is to automatically generate the value for SlugField fields from one or more other fields. The generated value is produced by concatenating the values of the source fields, and then by transforming that result into a valid slug (e.g. substituting dashes for spaces; lowercasing ASCII letters; and removing various English stop words such as ‘a’, ‘an’, ‘as’, and similar).

Prepopulated fields aren’t modified by JavaScript after a value has been saved. It’s usually undesired that slugs change (which would cause an object’s URL to change if the slug is used in it).

prepopulated_fields doesn’t accept DateTimeField, ForeignKey, OneToOneField, and ManyToManyField fields.

## `ModelAdmin.get_edit_handler()`

**Must return**: An instance of `wagtail.admin.panels.ObjectList`

Returns the appropriate `edit_handler` for the modeladmin class. `edit_handlers` can be defined either on the model itself or on the modeladmin (as property `edit_handler` or `panels`). Falls back to extracting panel / edit handler definitions from the model class.
