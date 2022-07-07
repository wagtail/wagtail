Contrib modules
===============

Wagtail ships with a variety of extra optional modules.


.. toctree::
    :maxdepth: 2

    settings
    forms/index
    sitemaps
    frontendcache
    routablepage
    modeladmin/index
    searchpromotions
    simple_translation
    table_block
    typed_table_block
    redirects
    legacy_richtext


:doc:`settings`
---------------

Settings that are editable by administrators within the Wagtail admin - either
site-specific or generic across all sites.


:doc:`forms/index`
------------------

Allows forms to be created by admins and provides an interface for browsing form submissions.


:doc:`sitemaps`
---------------

Provides a view that generates a Google XML sitemap of your public Wagtail content.


:doc:`frontendcache`
--------------------

A module for automatically purging pages from a cache (Varnish, Squid, Cloudflare or Cloudfront) when their content is changed.


:doc:`routablepage`
-------------------

Provides a way of embedding Django URLconfs into pages.


:doc:`modeladmin/index`
-----------------------

A module allowing for more customisable representation and management of custom models in Wagtail's admin area.


:doc:`searchpromotions`
-----------------------

A module for managing "Promoted Search Results"


:doc:`simple_translation`
-------------------------

A module for copying translatables (pages and snippets) to another language.


:doc:`table_block`
-----------------------

Provides a TableBlock for adding HTML tables to pages.


:doc:`typed_table_block`
------------------------

Provides a StreamField block for authoring tables, where cells can be any block type including rich text.


:doc:`redirects`
-----------------------

Provides a way to manage redirects.


:doc:`legacy_richtext`
-----------------------

Provides the legacy richtext wrapper (``<div class="rich-text"></div>``).
