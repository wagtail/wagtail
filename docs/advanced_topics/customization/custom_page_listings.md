(custom_page_listings)=

# Customizing page listings

(custom_default_page_listings)=

## Customizing the default page listings

```{versionadded} 7.4
The ability to customize the page explorer listing was added.
```

The page explorer is the default listing of pages in the Wagtail admin, where editors can navigate through the structure of the page tree. The pages in the tree can be of different types, thus only a limited set of fields common to all pages are available for display, filtering, and ordering. Wagtail provides a default set of columns and filters for the page explorer, but you may want to customize them to cater to your editors' needs.

To customize the default page explorer listing, create a subclass of {class}`~wagtail.admin.viewsets.pages.PageViewSet` and register it using the [`register_admin_viewset`](register_admin_viewset) hook. For example, to add a column for the `slug` field on all page listings, you could add the following definitions to a `wagtail_hooks.py` file within the app:

```python
# myapp/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.pages import PageViewSet
from wagtail.models import Page


class CustomPageViewSet(PageViewSet):
    columns = PageViewSet.columns.copy() + [
        Column("slug", label="Slug", sort_key="slug"),
    ]


custom_page_viewset = CustomPageViewSet()
@hooks.register("register_admin_viewset")
def register_custom_page_viewset():
    return custom_page_viewset
```

The filtering options for the listing can be customized by overriding the `filterset_class` attribute on the viewset. For example, you could add a filter for the `slug` field as follows:

```python
from wagtail import hooks
from wagtail.admin.viewsets.pages import PageViewSet
from wagtail.models import Page


class CustomPageFilterSet(PageViewSet.filterset_class):
    class Meta:
        model = Page
        fields = ["slug"]


class CustomPageViewSet(PageViewSet):
    # ...
    filterset_class = CustomPageFilterSet
```

For some page types, you may have enforced that only a single page type can be created under a given parent page. For example, your site may implement a `BlogIndexPage` model with its {attr}`~wagtail.models.Page.subpage_types` set to only allow `BlogPage` instances under it. With the listing limited to `BlogPage` instances, you can display, filter, and order on additional fields specific to `BlogPage` when viewing the children of a `BlogIndexPage`.

To customize the page explorer listing for a given parent page, set the `model` and `parent_models` attributes on a custom `PageViewSet` subclass. The following is an example of a custom viewset that adds a column and a filter for the `blog_category` field on the listing of `BlogPage` instances under a `BlogIndexPage`:

```python
# myapp/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.pages import PageViewSet

from myapp.models import BlogIndexPage, BlogPage


class BlogPageFilterSet(PageViewSet.filterset_class):
    class Meta:
        model = BlogPage
        fields = ["blog_category"]


class BlogPageViewSet(PageViewSet):
    model = BlogPage
    parent_models = [BlogIndexPage]
    columns = PageViewSet.columns.copy() + [
        Column("blog_category", label="Category", sort_key="blog_category"),
    ]
    filterset_class = BlogPageFilterSet


blog_page_viewset = BlogPageViewSet()
@hooks.register("register_admin_viewset")
def register_blog_page_viewset():
    return blog_page_viewset
```

Normally, editors navigate through the Wagtail admin interface by following the structure of the page tree. However, this can make it slow to locate a specific page for editing, especially on large sites where pages are organised into a deep hierarchy.

By default, Wagtail also provides a flat listing for each page type that can be accessed from the page types usage report. If you have registered a custom `PageViewSet` to customize the page explorer listing for a specific page type (as described in the above section), then all customizations you have made will also be applied to the flat listing for that page type.

Various other options are available for customizing the page listings, such as the `list_per_page` attribute to control how many items are shown per page, and the `ordering` attribute to control the default ordering of items in the listing. See the documentation for {class}`~wagtail.admin.viewsets.pages.PageViewSet` for more details.

(custom_flat_page_listings)=

## Creating custom flat page listings

In addition to the default page explorer and flat per-page-type listings, you can also create your own custom flat listings of all pages of a given type. This custom listing can be accessed from a menu item in the Wagtail admin menu, with the ability for editors to search and filter this list to find the pages they are interested in. To define a custom page listing, create a subclass of {class}`~wagtail.admin.viewsets.pages.PageListingViewSet` and register it using the [`register_admin_viewset`](register_admin_viewset) hook.

For example, if your site implemented the page type `BlogPage`, you could provide a "Blog pages" listing in the Wagtail admin by adding the following definitions to a `wagtail_hooks.py` file within the app:

```python
# myapp/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.viewsets.pages import PageListingViewSet

from myapp.models import BlogPage


class BlogPageListingViewSet(PageListingViewSet):
    icon = "globe"
    menu_label = "Blog Pages"
    add_to_admin_menu = True
    model = BlogPage


blog_page_listing_viewset = BlogPageListingViewSet("blog_pages")
@hooks.register("register_admin_viewset")
def register_blog_page_listing_viewset():
    return blog_page_listing_viewset
```

The columns of the listing can be customized by overriding the `columns` attribute on the viewset. This should be a list of `wagtail.admin.ui.tables.Column` instances:

```python
from wagtail import hooks
from wagtail.admin.ui.tables import Column
from wagtail.admin.viewsets.pages import PageListingViewSet

from myapp.models import BlogPage

class BlogPageListingViewSet(PageListingViewSet):
    # ...
    columns = PageListingViewSet.columns + [
        Column("blog_category", label="Category", sort_key="blog_category"),
    ]
```

The filtering options for the listing can be customized by overriding the `filterset_class` attribute on the viewset:

```python
from wagtail import hooks
from wagtail.admin.viewsets.pages import PageListingViewSet

from myapp.models import BlogPage


class BlogPageFilterSet(PageListingViewSet.filterset_class):
    class Meta:
        model = BlogPage
        fields = ["blog_category"]


class BlogPageListingViewSet(PageListingViewSet):
    # ...
    filterset_class = BlogPageFilterSet
```
