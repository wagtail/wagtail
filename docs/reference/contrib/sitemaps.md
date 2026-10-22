(sitemap_generation)=

# Sitemap generator

This document describes how to create XML sitemaps for your Wagtail website
using the `wagtail.contrib.sitemaps` module, which builds on Django's
[sitemap framework](inv:django#ref/contrib/sitemaps).

## Basic configuration

You firstly need to add `"django.contrib.sitemaps"` to INSTALLED_APPS in your
Django settings file:

```python
INSTALLED_APPS = [
    ...

    "django.contrib.sitemaps",
]
```

Then, in `urls.py`, you need to add a link to the
`wagtail.contrib.sitemaps.views.sitemap` view which generates the
sitemap. Use this view rather than Django's `django.contrib.sitemaps.views.sitemap`,
which doesn't know about Wagtail sites:

```python
from wagtail.contrib.sitemaps.views import sitemap

urlpatterns = [
    ...

    path("sitemap.xml", sitemap),

    ...

    # Ensure that the 'sitemap' line appears above the default Wagtail page serving route
    path("", include(wagtail_urls)),
]
```

You should now be able to browse to `/sitemap.xml` and see the sitemap
working. By default, it lists all published pages of your site, except private pages.

To help search engines and other crawlers find the sitemap, list it in your
`robots.txt`:

```text
Sitemap: https://mysite.com/sitemap.xml
```

(sitemap_caching)=

## Caching

The sitemap is generated on each request. To cache it, wrap the view in
Django's {func}`~django.views.decorators.cache.cache_page` decorator, as in
[Django's sitemap documentation](<inv:django:std:label#ref/contrib/sitemaps:creating a sitemap index>):

```python
from django.views.decorators.cache import cache_page

from wagtail.contrib.sitemaps.views import sitemap

urlpatterns = [
    ...

    path("sitemap.xml", cache_page(60 * 60)(sitemap)),

    ...

    # Ensure that the 'sitemap' line appears above the default Wagtail page serving route
    path("", include(wagtail_urls)),
]
```

This stores the sitemap in Django's cache for an hour and sets a `Cache-Control: max-age` header so that CDNs and
crawlers can cache it too. Pages published or unpublished in that time
won't be reflected until the cache expires, so pick a timeout that suits how
often your content changes.

The [frontend cache invalidator](frontend_cache_purging) doesn't purge the
sitemap when pages are published. If you [purge the sitemap URL](frontend_cache_invalidating_urls)
yourself, for example from a [`page_published`](signal_page_published) signal handler, use {func}`~django.views.decorators.cache.cache_control` instead,
for example `cache_control(max_age=60 * 60)(sitemap)`, since Django's cache
isn't purged.

## Setting the hostname

By default, the sitemap uses the hostname defined in the Wagtail Admin's
`Sites` area. If your default site is called `localhost`, then URLs in the
sitemap will look like:

```xml
<url>
    <loc>http://localhost/about/</loc>
    <lastmod>2015-09-26</lastmod>
</url>
```

For search engines to properly index your site, you need to set
a valid, crawlable hostname. If you change the site's hostname from
`localhost` to `mysite.com`, `sitemap.xml` will contain the correct URLs. If you
change the site's port to `443`, the `https` scheme will be used:

```xml
<url>
    <loc>https://mysite.com/about/</loc>
    <lastmod>2015-09-26</lastmod>
</url>
```

Find out more about [working with Sites](site_model_ref).

(sitemap_multi_language_support)=

## Multi-language support

When `WAGTAIL_I18N_ENABLED` is `True`, the sitemap includes pages from the page trees of all locales of the site, including pages that only exist in one locale, and alternate links will be automatically added for translations of each page.

```xml
<url>
    <loc>http://mysite.com/en/</loc>
    <lastmod>2025-03-15</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="http://mysite.com/en/"/>
    <xhtml:link rel="alternate" hreflang="fr" href="http://mysite.com/fr/"/>
</url>
<url>
    <loc>http://mysite.com/fr/</loc>
    <lastmod>2025-03-15</lastmod>
    <xhtml:link rel="alternate" hreflang="en" href="http://mysite.com/en/"/>
    <xhtml:link rel="alternate" hreflang="fr" href="http://mysite.com/fr/"/>
</url>
```

This behaviour can be disabled by passing `{"alternates": False}` when defining the URL pattern:

```python
# /my_project/urls.py

# ...

urlpatterns = [
    ...
    path("sitemap.xml", sitemap, {"alternates": False}),
    ...
]
```

## Customizing

### URLs

The `Page` class defines a `get_sitemap_urls` method which you can
override to customize sitemaps per `Page` instance. This method must accept
a request object and return a list of dictionaries, one dictionary per URL
entry in the sitemap. You can exclude pages from the sitemap by returning an
empty list.

Each dictionary can contain the following:

-   **location** (required) - This is the full URL path to add into the sitemap.
-   **lastmod** - A python date or datetime set to when the page was last modified.
-   **changefreq**
-   **priority**
-   **alternates** - A list of dicts containing `location` and `lang_code` items, indicating translations of the page.

You can add more but you will need to override the
`sitemap.xml` template in order for them to be displayed in the sitemap.

## Serving multiple sitemaps

Use a sitemap index if your site has more than 50,000 pages, or to add sitemaps
for content that isn't Wagtail pages, such as your own Django models.

To set one up, follow [Creating a sitemap index](<inv:django:std:label#ref/contrib/sitemaps:creating a sitemap index>)
in the Django documentation, but use the `index` and `sitemap` views from
`wagtail.contrib.sitemaps.views` instead of the ones from `django.contrib.sitemaps.views`.
To cache them, wrap both views in `cache_page`, as described in [](sitemap_caching).
