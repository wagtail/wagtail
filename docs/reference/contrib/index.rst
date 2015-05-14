Contrib modules
===============

Wagtail ships with a variety of extra optional modules. 


.. toctree::
    :maxdepth: 2

    staticsitegen
    sitemaps
    frontendcache
    routablepage
    api/index


``wagtailmedusa``
-----------------

:doc:`staticsitegen`

Provides a management command that turns a Wagtail site into a set of static HTML files.


``wagtailsitemaps``
-------------------

:doc:`sitemaps`

Provides a view that generates a Google XML sitemap of your public wagtail content.


``wagtailfrontendcache``
------------------------

:doc:`frontendcache`

A module for automatically purging pages from a cache (Varnish, Squid or Cloudflare) when their content is changed.


``wagtailroutablepage``
-----------------------

:doc:`routablepage`

Provides a way of embedding Django URLconfs into pages.


``wagtailapi``
--------------

:doc:`api/index`

A module for adding a read only, JSON based web API to your Wagtail site
