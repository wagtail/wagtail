.. _sitemap_generation:

Sitemap generator
=================

This document describes how to create XML sitemaps for your Wagtail website using the ``wagtail.contrib.wagtailsitemaps`` module.


Basic configuration
~~~~~~~~~~~~~~~~~~~

You firstly need to add ``"wagtail.contrib.wagtailsitemaps"`` to INSTALLED_APPS in your Django settings file:

 .. code-block:: python

    INSTALLED_APPS = [
        ...

        "wagtail.contrib.wagtailsitemaps",
    ]


Then, in ``urls.py``, you need to add a link to the ``wagtail.contrib.wagtailsitemaps.views.sitemap`` view which generates the sitemap:

.. code-block:: python

    from wagtail.contrib.wagtailsitemaps.views import sitemap

    urlpatterns = [
        ...

        url('^sitemap\.xml$', sitemap),

        ...

        # Ensure that the 'sitemap' line appears above the default Wagtail page serving route
        url(r'', include(wagtail_urls)),
    ]


You should now be able to browse to ``/sitemap.xml`` and see the sitemap working. By default, all published pages in your website will be added to the site map.


Setting the hostname
~~~~~~~~~~~~~~~~~~~~

By default, the sitemap uses the hostname defined in the Wagtail Admin's ``Sites`` area. If your
default site is called ``localhost``, then URLs in the sitemap will look like:

 .. code-block:: xml

    <url>
        <loc>http://localhost/about/</loc>
        <lastmod>2015-09-26</lastmod>
    </url>


For tools like Google Search Tools to properly index your site, you need to set a valid, crawlable hostname. If you change the site's hostname from ``localhost`` to ``mysite.com``, ``sitemap.xml``
will contain the correct URLs:

 .. code-block:: xml

    <url>
        <loc>http://mysite.com/about/</loc>
        <lastmod>2015-09-26</lastmod>
    </url>


Find out more about :ref:`working with Sites<site-model-ref>`.


Customising
~~~~~~~~~~~

URLs
----

The ``Page`` class defines a ``get_sitemap_urls`` method which you can override to customise sitemaps per ``Page`` instance. This method must return a list of dictionaries, one dictionary per URL entry in the sitemap. You can exclude pages from the sitemap by returning an empty list.

Each dictionary can contain the following:

 - **location** (required) - This is the full URL path to add into the sitemap.
 - **lastmod** - A python date or datetime set to when the page was last modified.
 - **changefreq**
 - **priority**

You can add more but you will need to override the ``wagtailsitemaps/sitemap.xml`` template in order for them to be displayed in the sitemap.


Cache
-----

By default, sitemaps are cached for 100 minutes. You can change this by setting ``WAGTAILSITEMAPS_CACHE_TIMEOUT`` in your Django settings to the number of seconds you would like the cache to last for.
