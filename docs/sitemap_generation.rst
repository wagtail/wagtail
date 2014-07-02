Sitemap generation
==================

This document describes how to create XML sitemaps for your Wagtail website using the ``wagtail.contrib.wagtailsitemaps`` module.


Basic configuration
~~~~~~~~~~~~~~~~~~~

You firstly need to add ``"wagtail.contrib.wagtailsitemaps"`` to INSTALLED_APPS in your Django settings file:

 .. code-block:: python

    INSTALLED_APPS = [
        ...

        "wagtail.contrib.wagtailsitemaps",
    ]


Then, in urls.py, you need to add a link to the ``wagtail.contrib.wagtailsitemaps.views.sitemap`` view which generates the sitemap:

.. code-block:: python

    from wagtail.contrib.wagtailsitemaps.views import sitemap

    urlpatterns = patterns('',
        ...

        url('^sitemap\.xml$', sitemap),
    )


You should now be able to browse to "/sitemap.xml" and see the sitemap working. By default, all published pages in your website will be added to the site map.


Customising
~~~~~~~~~~~

URLs
----

The Page class defines a ``get_sitemap_urls`` method which you can override to customise sitemaps per page instance. This method must return a list of dictionaries, one dictionary per URL entry in the sitemap. You can exclude pages from the sitemap by returning an empty list.

Each dictionary can contain the following:

 - **location** (required) - This is the full URL path to add into the sitemap.
 - **lastmod** - A python date or datetime set to when the page was last modified.
 - **changefreq**
 - **priority**

You can add more but you will need to override the ``wagtailsitemaps/sitemap.xml`` template in order for them to be displayed in the sitemap.


Cache
-----

By default, sitemaps are cached for 100 minutes. You can change this by setting ``WAGTAILSITEMAPS_CACHE_TIMEOUT`` in your Django settings to the number of seconds you would like the cache to last for.
