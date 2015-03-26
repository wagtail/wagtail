Contrib modules
===============

Wagtail ships with a variety of extra optional modules. 


.. toctree::
    :maxdepth: 2

    static_site_generation
    sitemap_generation
    frontendcache
    routablepage


``wagtailmedusa``
-----------------

:doc:`static_site_generation`

Provides a management command that turns a Wagtail site into a set of static HTML files.


``wagtailsitemaps``
-------------------

:doc:`sitemap_generation`

Provides a view that generates a Google XML sitemap of your public wagtail content.


``wagtailfrontendcache``
------------------------

:doc:`frontendcache`

A module for automatically purging pages from a cache (Varnish, Squid or Cloudflare) when their content is changed.


``wagtailroutablepage``
-----------------------

:doc:`routablepage`

Provides a way of embedding Django URLconfs into pages.
