(custom_page_listings)=

# Custom page listings

Normally, editors navigate through the Wagtail admin interface by following the structure of the page tree. However, this can make it slow to locate a specific page for editing, especially on large sites where pages are organised into a deep hierarchy.

Custom page listings are a way to present a flat list of all pages of a given type, accessed from a menu item in the Wagtail admin menu, with the ability for editors to search and filter this list to find the pages they are interested in. To define a custom page listing, create a subclass of {class}`~wagtail.admin.viewsets.pages.PageListingViewSet` and register it using the [`register_admin_viewset`](register_admin_viewset) hook.

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
