# Migrating from ModelAdmin to Snippets

To provide a single, unified way to manage non-page Django models, the `modeladmin` contrib module has been deprecated in favor of the `snippets` module. This page explains how to migrate from `modeladmin` to `snippets`.

## Installation

Ensure `wagtail.snippets` is in your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...,
    'wagtail.snippets',
    ...,
]
```

## Convert `ModelAdmin` class to `SnippetViewSet`

```{eval-rst}
.. module:: wagtail.snippets.views.snippets
    :noindex:
```

The {class}`~SnippetViewSet` class is the snippets-equivalent to the `ModelAdmin` class. To migrate a `ModelAdmin` class to a `SnippetViewSet` class, follow these instructions.

Change any imports of `ModelAdmin` and `modeladmin_register` to `SnippetViewSet` and `register_snippet`, respectively:

```diff
- from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
+ from wagtail.snippets.models import register_snippet
+ from wagtail.snippets.views.snippets import SnippetViewSet
```

Change any references to `ModelAdmin` and `modeladmin_register` to `SnippetViewSet` and `register_snippet`, respectively:

```diff
- class MyModelAdmin(ModelAdmin):
+ class MySnippetViewSet(SnippetViewSet):
      ...

- modeladmin_register(MyModelAdmin)
+ register_snippet(MySnippetViewSet)
```

There are a few attributes of `ModelAdmin` that need to be renamed/adjusted for `SnippetViewSet`. The following is a table of such attributes and the changes that need to be made:

| `ModelAdmin` attribute | `SnippetViewSet` attribute | Notes |
| ---------------------- | -------------------------- | ----- |
| `add_to_admin_menu`    | {attr}`~SnippetViewSet.add_to_admin_menu`        | Same attribute name, but the value defaults to `False` instead of `True`. Set to `True` to add a top-level menu item for the model. |
| `menu_icon`            | {attr}`~SnippetViewSet.icon`                     | Same value, but different attribute name, as the icon is used throughout the admin and not just in the menu. |
| `list_display`         | {attr}`~wagtail.admin.viewsets.model.ModelViewSet.list_display`             | Same attribute name, but the list/tuple of strings must refer to existing attributes or methods on the model, not the `SnippetViewSet` class. If you have specified a string that refers to an attribute or method on the `ModelAdmin` class, you need to move it to the model. In addition, `list_display` now also supports instances of the `wagtail.admin.ui.tables.Column` component class. |
| `list_filter`          | {attr}`~SnippetViewSet.list_filter`              | Same attribute name and value, but filtering is built on top of the django-filter package under the hood, which behaves differently to ModelAdmin's filters. See documentation for `SnippetViewSet.list_filter` and {attr}`~SnippetViewSet.filterset_class` for more details. |
| `form_fields_exclude`  | {attr}`~wagtail.admin.viewsets.model.ModelViewSet.exclude_form_fields`           | Same value, but different attribute name to better align with `ModelViewSet`. |
| - | {attr}`~SnippetViewSet.template_prefix` | New attribute. Set to the name of a template directory to override the `"wagtailsnippets/snippets/"` default. If set to `"modeladmin/"`, the template directory structure will be equal to what ModelAdmin uses. Make sure any custom templates are placed in the correct directory according to this prefix. See [](wagtailsnippets_templates) for more details. |

### Boolean properties in `list_display`

In ModelAdmin, boolean fields in `list_display` are rendered as tick/cross icons. To achieve the same behavior in SnippetViewSet, you need to use a `wagtail.admin.ui.tables.BooleanColumn` instance in `SnippetViewSet.list_display`:

```python
from wagtail.admin.ui.tables import BooleanColumn


class MySnippetViewSet(SnippetViewSet):
    list_display = ("title", BooleanColumn("is_active"))
```

The `BooleanColumn` class works with both model fields and custom properties that return booleans.

```{versionadded} 5.1.1
The `BooleanColumn` class was added.
```

## Convert `ModelAdminGroup` class to `SnippetViewSetGroup`

The {class}`~SnippetViewSetGroup` class is the snippets-equivalent to the `ModelAdminGroup` class. To migrate a `ModelAdminGroup` class to a `SnippetViewSetGroup` class, follow these instructions.

Change any imports of `ModelAdminGroup` to `SnippetViewSetGroup`:

```diff
- from wagtail.contrib.modeladmin.options import ModelAdminGroup
+ from wagtail.snippets.views.snippets import SnippetViewSetGroup
```

Change any references to `ModelAdminGroup` to `SnippetViewSetGroup`:

```diff
- class MyModelAdminGroup(ModelAdminGroup):
+ class MySnippetViewSetGroup(SnippetViewSetGroup):
      ...

- modeladmin_register(MyModelAdminGroup)
+ register_snippet(MySnippetViewSetGroup)
```

## Unsupported features and customizations

Some features and customizations in `ModelAdmin` are not directly supported via `SnippetViewSet`, but may be achievable via other means that are more in line with Wagtail's architecture.

### Using ModelAdmin to manage Page models

ModelAdmin allows the registration of Page models, but the main use case is to create custom page listing views. The create and edit views are not supported by ModelAdmin, as there are page-specific operations in those views that are best handled by Wagtail's page views. For this reason, registering a Page model as a snippet is not supported.

```{note}
In a future release, Wagtail will introduce a new "treeless" listing view for pages, as outlined in [RFC 082: Treeless page listings](https://github.com/wagtail/rfcs/pull/82) and the [Universal Listings discussion](https://github.com/wagtail/wagtail/discussions/10446). This feature will allow for custom page listing views and will be the recommended way to achieve this use case. Feedback to this upcoming feature is welcome.
```

### Customization of index view table rows and columns

ModelAdmin has a number of APIs that allow customization of the index view table rows and columns. Meanwhile, Wagtail has an internal generic tables UI framework that is used throughout the admin, including snippets. This table framework will become the standard way to build table elements in index views within the admin. As a result, the following APIs are not supported in snippets:

- `ModelAdmin.get_extra_attrs_for_row`

  This can be achieved by creating a custom `wagtail.admin.ui.tables.Table` subclass and using it as the `IndexView.table_class`.

- `ModelAdmin.get_extra_class_names_for_field_col`

  This can be achieved using a custom `wagtail.admin.ui.tables.Column` instance in `SnippetViewSet.list_display`.
- `ModelAdmin.list_display_add_buttons`

  By default, the first column specified in `list_display` is the one that contains the buttons. Using custom `wagtail.admin.ui.tables.Column` instances in `SnippetViewSet.list_display` allows you to specify a different column.

- Attributes for `wagtail.contrib.modeladmin.mixins.ThumbnailMixin`

  This mixin is used to show a thumbnail in the index view. A similar functionality can be achieved using a custom `wagtail.admin.ui.tables.Column` instance in `SnippetViewSet.list_display`. Hence, the following attributes are not supported:

    - `ModelAdmin.thumb_image_field_name`
    - `ModelAdmin.thumb_image_width`
    - `ModelAdmin.thumb_classname`
    - `ModelAdmin.thumb_col_header_text`
    - `ModelAdmin.thumb_default`

### Custom CSS and JS

ModelAdmin supports inserting custom extra CSS and JS files into the admin via the following attributes on the ModelAdmin class:

- `ModelAdmin.index_view_extra_css`
- `ModelAdmin.index_view_extra_js`
- `ModelAdmin.form_view_extra_css`
- `ModelAdmin.form_view_extra_js`
- `ModelAdmin.inspect_view_extra_css`
- `ModelAdmin.inspect_view_extra_js`

This is not supported in snippets, but custom CSS and JS files can be inserted by overriding the respective view's template. Alternatively, the [`insert_global_admin_css`](insert_global_admin_css) and [`insert_global_admin_js`](insert_global_admin_js) hooks can also be used.

### Helper classes

Helper classes encapsulate the logic that is commonly used across views in ModelAdmin. These classes do not exist for snippets, as the similar logic now relies on generic patterns used across Wagtail.

- `ModelAdmin.url_helper_class`

  The base {class}`~wagtail.admin.viewsets.base.ViewSet` class has {meth}`~wagtail.admin.viewsets.base.ViewSet.get_urlpatterns()` and {meth}`~wagtail.admin.viewsets.base.ViewSet.get_url_name()` methods that can be used to manage the URLs of snippets views. The URL names can be used with Django's `reverse()` function to generate URLs.

- `ModelAdmin.permission_helper_class`

  Wagtail uses an internal permission policy system to manage permissions across the admin. The {class}`~SnippetViewSet` class has a {attr}`~SnippetViewSet.permission_policy` attribute, which is an instance of a permission policy class.

- `ModelAdmin.button_helper_class`

  The pre-existing [`register_snippet_listing_buttons`](register_snippet_listing_buttons) and [`construct_snippet_listing_buttons`](construct_snippet_listing_buttons) hooks can be used to customize the buttons in the listing view. For other views, custom buttons can be added by overriding the respective view's template.

- `ModelAdmin.search_handler_class`

  When searching snippets, Wagtail's default search backend is used. To use a different backend, the {attr}`~SnippetViewSet.search_backend_name` attribute can be overridden. If the attribute is set to `None`, the search uses the Django ORM instead.

  As the `search_handler_class` attribute is not supported in snippets, the `ModelAdmin.extra_search_kwargs` attribute is also not supported.

### Other customizations

- `ModelAdmin.empty_value_display` and `ModelAdmin.get_empty_value_display()`

  This can be replaced by the Django-standard {meth}`~django.db.models.Model.get_FOO_display` method on the model.

- `ModelAdmin.get_ordering(request)`

  The {attr}`SnippetViewSet.ordering` attribute is responsible for the default ordering of the index view, before falling back to the model's {attr}`~django.db.models.Options.ordering`. The index view handles per-request ordering based on the columns that are specified in `list_display`. For more advanced customization, you can override the {attr}`~SnippetViewSet.index_view_class`.

- `ModelAdmin.prepopulated_fields`

  This is not supported in favor of [`TitleFieldPanel`](title_field_panel).

## Keep ModelAdmin usage

If you still rely on ModelAdmin, it is still available as a separate [wagtail-modeladmin](https://github.com/wagtail-nest/wagtail-modeladmin) package. The package is in maintenance mode and will not receive new features. If you have a use case that is not supported by `SnippetViewSet` and not described above, consider opening a feature request in the Wagtail issue tracker. For more details, see [](../../../contributing/issue_tracking).
