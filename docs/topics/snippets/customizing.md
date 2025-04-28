```{currentmodule} wagtail.snippets.views.snippets

```

(wagtailsnippets_custom_admin_views)=

# Customizing admin views for snippets

Additional customizations to the admin views for each snippet model can be achieved through a custom {class}`~SnippetViewSet` class. The `SnippetViewSet` is a subclass of {class}`.ModelViewSet`, with snippets-specific properties provided by default. Hence, it supports the same customizations provided by `ModelViewSet` such as customizing the listing view (e.g. adding custom columns, and filters), creating a custom menu item, and more.

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
# wagtail_hooks.py
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from myapp.models import Member, MemberFilterSet


class MemberViewSet(SnippetViewSet):
    model = Member
    icon = "user"
    list_display = ["name", "shirt_size", "get_shirt_size_display", UpdatedAtColumn()]
    list_per_page = 50
    copy_view_enabled = False
    inspect_view_enabled = True
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

You can define an {attr}`~.ViewSet.icon` attribute on the `SnippetViewSet` to specify the icon that is used across the admin for this snippet type. The `icon` needs to be [registered in the Wagtail icon library](../../advanced_topics/icons). If `icon` is not set, the default `"snippet"` icon is used.

## URL namespace and base URL path

The {attr}`~.ViewSet.url_namespace` property can be overridden to use a custom URL namespace for the URL patterns of the views. If unset, it defaults to `wagtailsnippets_{app_label}_{model_name}`. Meanwhile, overriding {attr}`~.ViewSet.url_prefix` allows you to customize the base URL path relative to the Wagtail admin URL. If unset, it defaults to `snippets/app_label/model_name`.

Similar URL customizations are also possible for the snippet chooser views through {attr}`~SnippetViewSet.chooser_admin_url_namespace`, {attr}`~SnippetViewSet.chooser_base_url_path`, {meth}`~SnippetViewSet.get_chooser_admin_url_namespace`, and {meth}`~SnippetViewSet.get_chooser_admin_base_path`.

## Listing view

You can customize the listing view to add custom columns, filters, pagination, etc. via various attributes available on the `SnippetViewSet`. Refer to [the listing view customizations for `ModelViewSet`](modelviewset_listing) for more details.

Additionally, you can customize the base queryset for the listing view by overriding the {meth}`~SnippetViewSet.get_queryset` method.

## Copy view

The copy view is enabled by default and will be accessible by users with the 'add' permission on the model. To disable it, set {attr}`~.ModelViewSet.copy_view_enabled` to `False`. Refer to [the copy view customizations for `ModelViewSet`](modelviewset_copy) for more details.

## Inspect view

The inspect view is disabled by default, as it's not often useful for most models. To enable it, set {attr}`~.ModelViewSet.inspect_view_enabled` to `True`. Refer to [the inspect view customizations for `ModelViewSet`](modelviewset_inspect) for more details.

(wagtailsnippets_templates)=

## Templates

Template customizations work the same way as for `ModelViewSet`, except that the {attr}`~.ModelViewSet.template_prefix` defaults to `wagtailsnippets/snippets/`. Refer to [the template customizations for `ModelViewSet`](modelviewset_templates) for more details.

(wagtailsnippets_menu_item)=

## Menu item

By default, registering a snippet model will add a "Snippets" menu item to the sidebar menu. However, you can configure a snippet model to have its own top-level menu item in the sidebar menu by setting {attr}`~.ViewSet.add_to_admin_menu` to `True`. Refer to [the menu customizations for `ModelViewSet`](modelviewset_menu) for more details.

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

Multiple snippet models can also be grouped under a single menu item using a {attr}`~SnippetViewSetGroup`. You can do this by setting the {attr}`~SnippetViewSet.model` attribute on the `SnippetViewSet` classes and then registering the `SnippetViewSetGroup` subclass instead of each individual model or viewset:

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
    menu_icon = "folder-inverse"
    menu_label = "Marketing"
    menu_name = "marketing"


# When using a SnippetViewSetGroup class to group several SnippetViewSet classes together,
# only register the SnippetViewSetGroup class. You do not need to register each snippet
# model or viewset separately.
register_snippet(MarketingViewSetGroup)
```

By default, the sidebar "Snippets" menu item will only show snippet models that haven't been configured with their own menu items.
If all snippet models have their own menu items, the "Snippets" menu item will not be shown.
This behaviour can be changed using the [](wagtailsnippets_menu_show_all) setting.

Various additional attributes are available to customize the viewset - see {class}`~SnippetViewSet`.
