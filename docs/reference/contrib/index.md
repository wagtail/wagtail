# Contrib modules

Wagtail ships with a variety of extra optional modules.

```{toctree}
---
maxdepth: 2
---
settings
forms/index
sitemaps
frontendcache
routablepage
searchpromotions
simple_translation
table_block
typed_table_block
redirects
legacy_richtext
```

## [](settings)

Settings that are editable by administrators within the Wagtail admin - either
site-specific or generic across all sites.

## [](forms/index)

Allows forms to be created by admins and provides an interface for browsing form submissions.

## [](sitemaps)

Provides a view that generates a Google XML sitemap of your public Wagtail content.

## [](frontendcache)

A module for automatically purging pages from a cache (Varnish, Squid, Cloudflare or CloudFront) when their content is changed.

## [](routablepage)

Provides a way of embedding Django URLconfs into pages.

## [](searchpromotions)

A module for managing "Promoted Search Results"

## [](simple_translation.md)

A module for copying translatables (pages and snippets) to another language.

## [](table_block)

Provides a TableBlock for adding HTML tables to pages.

## [](typed_table_block)

Provides a StreamField block for authoring tables, where cells can be any block type including rich text.

## [](redirects.md)

Provides a way to manage redirects.

## [](legacy_richtext)

Provides the legacy richtext wrapper (`<div class="rich-text"></div>`).
