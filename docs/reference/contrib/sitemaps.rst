.. _sitemap_generation:

Sitemap generator
=================

This document describes how to create XML sitemaps for your Wagtail website
using the ``wagtail.contrib.sitemaps`` module.


.. note::

    As of Wagtail 1.10 the Django contrib sitemap app is used to generate
    sitemaps.  However since Wagtail requires the Site instance to be available
    during the sitemap generation you will have to use the views from the
    ``wagtail.contrib.sitemaps.views`` module instead of the views
    provided by Django (``django.contrib.sitemaps.views``).

    The usage of these views is otherwise identical, which means that
    customisation and caching of the sitemaps are done using the default Django
    patterns.  See the Django documentation for in-depth information.


Basic configuration
~~~~~~~~~~~~~~~~~~~


You firstly need to add ``"django.contrib.sitemaps"`` to INSTALLED_APPS in your
Django settings file:

.. code-block:: python

  INSTALLED_APPS = [
      ...

      "django.contrib.sitemaps",
  ]


Then, in ``urls.py``, you need to add a link to the
``wagtail.contrib.sitemaps.views.sitemap`` view which generates the
sitemap:

.. code-block:: python

    from wagtail.contrib.sitemaps.views import sitemap

    urlpatterns = [
        ...

        path('sitemap.xml', sitemap),

        ...

        # Ensure that the 'sitemap' line appears above the default Wagtail page serving route
        re_path(r'', include(wagtail_urls)),
    ]


You should now be able to browse to ``/sitemap.xml`` and see the sitemap
working. By default, all published pages in your website will be added to the
site map.


Setting the hostname
~~~~~~~~~~~~~~~~~~~~

By default, the sitemap uses the hostname defined in the Wagtail Admin's
``Sites`` area. If your default site is called ``localhost``, then URLs in the
sitemap will look like:

.. code-block:: xml

  <url>
      <loc>http://localhost/about/</loc>
      <lastmod>2015-09-26</lastmod>
  </url>


For tools like Google Search Tools to properly index your site, you need to set
a valid, crawlable hostname. If you change the site's hostname from
``localhost`` to ``mysite.com``, ``sitemap.xml`` will contain the correct URLs:

.. code-block:: xml

  <url>
      <loc>http://mysite.com/about/</loc>
      <lastmod>2015-09-26</lastmod>
  </url>


If you change the site's port to ``443``, the ``https`` scheme will be used.
Find out more about :ref:`working with Sites<site-model-ref>`.


Customising
~~~~~~~~~~~

URLs
----

The ``Page`` class defines a ``get_sitemap_urls`` method which you can
override to customise sitemaps per ``Page`` instance. This method must accept
a request object and return a list of dictionaries, one dictionary per URL
entry in the sitemap. You can exclude pages from the sitemap by returning an
empty list.

Each dictionary can contain the following:

- **location** (required) - This is the full URL path to add into the sitemap.
- **lastmod** - A python date or datetime set to when the page was last modified.
- **changefreq**
- **priority**

You can add more but you will need to override the
``sitemap.xml`` template in order for them to be displayed in the sitemap.


Serving multiple sitemaps
~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to support the sitemap indexes from Django then you will need to
use the index view from ``wagtail.contrib.sitemaps.views`` instead of the index
view from ``django.contrib.sitemaps.views``.  Please see the Django
documentation for further details.
