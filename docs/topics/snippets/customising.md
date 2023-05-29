(wagtailsnippets_custom_admin_views)=

# Customising admin views for snippets

Additional customisations to the admin views for each snippet model can be achieved through a custom {class}`~wagtail.snippets.views.snippets.SnippetViewSet` class. This allows you to customise the listing view (e.g. adding custom columns, filters), create a custom menu item, and more.

Before proceeding, ensure that you register the snippet model using `register_snippet` as a function instead of a decorator, as described in [](wagtailsnippets_registering).

For demonstration, consider the following `Member` model and a `MemberFilterSet` class:

```python
# models.py
from django.db import models
from wagtail.admin.filters import WagtailFilterSet


class Member(models.Model):
    class ShirtSize(models.TextChoices):
        SMALL = "S", "Small"
        MEDIUM = "M", "Medium"
        LARGE = "L", "Large"
        EXTRA_LARGE = "XL", "Extra Large"

    name = models.CharField(max_length=255)
    shirt_size = models.CharField(max_length=5, choices=ShirtSize.choices, default=ShirtSize.MEDIUM)

    def get_shirt_size_display(self):
        return self.ShirtSize(self.shirt_size).label

    get_shirt_size_display.admin_order_field = "shirt_size"
    get_shirt_size_display.short_description = "Size description"


class MemberFilterSet(WagtailFilterSet):
    class Meta:
        model = Member
        fields = ["shirt_size"]
```

And the following is the snippet's corresponding `SnippetViewSet` subclass:

```python
from wagtail.admin.panels import FieldPanel
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from myapp.models import Member, MemberFilterSet


class MemberViewSet(SnippetViewSet):
    model = Member
    icon = "user"
    list_display = ["name", "shirt_size", "get_shirt_size_display", UpdatedAtColumn()]
    list_per_page = 50
    admin_url_namespace = "member_views"
    base_url_path = "internal/member"
    filterset_class = MemberFilterSet
    # alternatively, you can use the following instead of filterset_class
    # list_filter = ["shirt_size"]
    # or
    # list_filter = {"shirt_size": ["exact"], "name": ["icontains"]}

    edit_handler = TabbedInterface([
        ObjectList([FieldPanel("name")], heading="Details"),
        ObjectList([FieldPanel("shirt_size")], heading="Preferences"),
    ])

register_snippet(MemberViewSet)
```

(wagtailsnippets_icon)=

## Icon

You can define an {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.icon` attribute on the `SnippetViewSet` to specify the icon that is used across the admin for this snippet type. The `icon` needs to be [registered in the Wagtail icon library](../../advanced_topics/icons). If `icon` is not set, the default `"snippet"` icon is used.

## URL namespace and base URL path

The {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.admin_url_namespace` attribute can be set to use a custom URL namespace for the URL patterns of the views. If unset, it defaults to `wagtailsnippets_{app_label}_{model_name}`. Meanwhile, setting {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.base_url_path` allows you to customise the base URL path relative to the Wagtail admin URL. If unset, it defaults to `snippets/app_label/model_name`.

If you need further customisations, you can also override the {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_admin_url_namespace` and {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_admin_base_path` methods to override the namespace and base URL path, respectively.

Similar URL customisations are also possible for the snippet chooser views through {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.chooser_admin_url_namespace`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.chooser_base_url_path`, {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_chooser_admin_url_namespace`, and {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_chooser_admin_base_path`.

## Listing view

The {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.list_display` attribute can be set to specify the columns shown on the listing view. To customise the number of items to be displayed per page, you can set the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.list_per_page` attribute (or {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.chooser_per_page` for the chooser listing).

To customise the base queryset for the listing view, you could override the {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_queryset` method. Additionally, the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.ordering` attribute can be used to specify the default ordering of the listing view.

You can add the ability to filter the listing view by defining a {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.list_filter` attribute and specifying the list of fields to filter. Wagtail uses the django-filter package under the hood, and this attribute will be passed as django-filter's `FilterSet.Meta.fields` attribute. This means you can also pass a dictionary that maps the field name to a list of lookups.

If you would like to make further customisations to the filtering mechanism, you can also use a custom `wagtail.admin.filters.WagtailFilterSet` subclass by overriding the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.filterset_class` attribute. The `list_filter` attribute is ignored if `filterset_class` is set. For more details, refer to [django-filter's documentation](https://django-filter.readthedocs.io/en/stable/guide/usage.html#the-filter).

## Templates

For all views that are used for a snippet model, Wagtail looks for templates in the following directories within your project or app, before resorting to the defaults:

1. `templates/wagtailsnippets/snippets/{app_label}/{model_name}/`
2. `templates/wagtailsnippets/snippets/{app_label}/`
3. `templates/wagtailsnippets/snippets/`

So, to override the template used by the `IndexView` for example, you could create a new `index.html` template and put it in one of those locations. For example, if you wanted to do this for a `Shirt` model in a `shirts` app, you could add your custom template as `shirts/templates/wagtailsnippets/snippets/shirts/shirt/index.html`. You could change the `wagtailsnippets/snippets/` prefix for the templates by overriding the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.template_prefix` attribute.

For some common views, Wagtail also allows you to override the template used by either specifying the `{view_name}_template_name` attribute or overriding the `get_{view_name}_template()` method on the viewset. The following is a list of customisation points for the views:

-   `IndexView`: `index.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.index_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_index_template()`
    -   For the results fragment used in AJAX responses (e.g. when searching), customise `index_results.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.index_results_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_index_results_template()`.
-   `CreateView`: `create.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.create_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_create_template()`
-   `EditView`: `edit.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.edit_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_edit_template()`
-   `DeleteView`: `delete.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.delete_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_delete_template()`
-   `HistoryView`: `history.html`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.history_template_name`, or {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_history_template()`

## Menu item

```{versionadded} 5.0
The ability to have a separate menu item was added.
```

By default, registering a snippet model will add a "Snippets" menu item to the sidebar menu. You can configure a snippet model to have its own top-level menu item in the sidebar menu by setting {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.add_to_admin_menu` to `True`. Alternatively, if you want to add the menu item inside the Settings menu, you can set {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.add_to_settings_menu` to `True`. The menu item will use the icon specified on the `SnippetViewSet` and it will link to the index view for the snippet model.

Unless specified, the menu item will be named after the model's verbose name. You can customise the menu item's label, name, and order by setting the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.menu_label`, {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.menu_name`, and {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.menu_order` attributes respectively. If you would like to customise the `MenuItem` instance completely, you could override the {meth}`~wagtail.snippets.views.snippets.SnippetViewSet.get_menu_item` method.

An example of a custom `SnippetViewSet` subclass with `add_to_admin_menu` set to `True`:

```python
from wagtail.snippets.views.snippets import SnippetViewSet


class AdvertViewSet(SnippetViewSet):
    model = Advert
    icon = "crosshairs"
    menu_label = "Advertisements"
    menu_name = "adverts"
    menu_order = 300
    add_to_admin_menu = True
```

Multiple snippet models can also be grouped under a single menu item using a {attr}`~wagtail.snippets.views.snippets.SnippetViewSetGroup`. You can do this by setting the {attr}`~wagtail.snippets.views.snippets.SnippetViewSet.model` attribute on the `SnippetViewSet` classes and then registering the `SnippetViewSetGroup` subclass instead of each individual model or viewset:

```python
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup


class AdvertViewSet(SnippetViewSet):
    model = Advert
    icon = "crosshairs"
    menu_label = "Advertisements"
    menu_name = "adverts"


class ProductViewSet(SnippetViewSet):
    model = Product
    icon = "desktop"
    menu_label = "Products"
    menu_name = "banners"


class MarketingViewSetGroup(SnippetViewSetGroup):
    items = (AdvertViewSet, ProductViewSet)
    icon = "folder-inverse"
    menu_label = "Marketing"
    menu_name = "marketing"


# When using a SnippetViewSetGroup class to group several SnippetViewSet classes together,
# only register the SnippetViewSetGroup class. You do not need to register each snippet
# model or viewset separately.
register_snippet(MarketingViewSetGroup)
```

If all snippet models have their own menu items, the "Snippets" menu item will not be shown.

Various additional attributes are available to customise the viewset - see {class}`~wagtail.snippets.views.snippets.SnippetViewSet`.
