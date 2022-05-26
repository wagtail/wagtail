# Wagtail API v2 Usage Guide

The Wagtail API module exposes a public, read only, JSON-formatted API which
can be used by external clients (such as a mobile app) or the site's frontend.

This document is intended for developers using the API exposed by Wagtail. For
documentation on how to enable the API module in your Wagtail site, see
[Wagtail API v2 Configuration Guide](/advanced_topics/api/v2/configuration)

Contents

```{contents}
---
local:
depth: 3
---
```

## Fetching content

To fetch content over the API, perform a `GET` request against one of the
following endpoints:

-   Pages `/api/v2/pages/`
-   Images `/api/v2/images/`
-   Documents `/api/v2/documents/`

```{note}
The available endpoints and their URLs may vary from site to site, depending
on how the API has been configured.
```

### Example response

Each response contains the list of items (`items`) and the total count
(`meta.total_count`). The total count is irrespective of pagination.

```text
GET /api/v2/endpoint_name/

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": "total number of results"
    },
    "items": [
        {
            "id": 1,
            "meta": {
                "type": "app_name.ModelName",
                "detail_url": "http://api.example.com/api/v2/endpoint_name/1/"
            },
            "field": "value"
        },
        {
            "id": 2,
            "meta": {
                "type": "app_name.ModelName",
                "detail_url": "http://api.example.com/api/v2/endpoint_name/2/"
            },
            "field": "different value"
        }
    ]
}
```

(apiv2_custom_page_fields)=

### Custom page fields in the API

Wagtail sites contain many page types, each with their own set of fields. The
`pages` endpoint will only expose the common fields by default (such as
`title` and `slug`).

To access custom page fields with the API, select the page type with the
`?type` parameter. This will filter the results to only include pages of that
type but will also make all the exported custom fields for that type available
in the API.

For example, to access the `published_date`, `body` and `authors` fields
on the `blog.BlogPage` model in the [configuration docs](apiv2_page_fields_configuration):

```
GET /api/v2/pages/?type=blog.BlogPage&fields=published_date,body,authors(name)

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 10
    },
    "items": [
        {
            "id": 1,
            "meta": {
                "type": "blog.BlogPage",
                "detail_url": "http://api.example.com/api/v2/pages/1/",
                "html_url": "http://www.example.com/blog/my-blog-post/",
                "slug": "my-blog-post",
                "first_published_at": "2016-08-30T16:52:00Z"
            },
            "title": "Test blog post",
            "published_date": "2016-08-30",
            "authors": [
                {
                    "id": 1,
                    "meta": {
                        "type": "blog.BlogPageAuthor",
                    },
                    "name": "Karl Hobley"
                }
            ]
        },

        ...
    ]
}
```

```{note}
Only fields that have been explicitly exported by the developer may be used
in the API. This is done by adding a `api_fields` attribute to the page
model. You can read about configuration [here](apiv2_page_fields_configuration).
```

This doesn't apply to images/documents as there is only one model exposed in
those endpoints. But for projects that have customized image/document models,
the `api_fields` attribute can be used to export any custom fields into the
API.

### Pagination

The number of items in the response can be changed by using the `?limit`
parameter (default: 20) and the number of items to skip can be changed by using
the `?offset` parameter.

For example:

```
GET /api/v2/pages/?offset=20&limit=20

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 50
    },
    "items": [
        pages 20 - 40 will be listed here.
    ]
}
```

```{note}
There may be a maximum value for the `?limit` parameter. This can be
modified in your project settings by setting `WAGTAILAPI_LIMIT_MAX` to
either a number (the new maximum value) or `None` (which disables maximum
value check).
```

### Ordering

The results can be ordered by any field by setting the `?order` parameter to
the name of the field to order by.

```
GET /api/v2/pages/?order=title

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 50
    },
    "items": [
        pages will be listed here in ascending title order (a-z)
    ]
}
```

The results will be ordered in ascending order by default. This can be changed
to descending order by prefixing the field name with a `-` sign.

```
GET /api/v2/pages/?order=-title

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 50
    },
    "items": [
        pages will be listed here in descending title order (z-a)
    ]
}
```

```{note}
Ordering is case-sensitive so lowercase letters are always ordered after
uppercase letters when in ascending order.
```

#### Random ordering

Passing `random` into the `?order` parameter will make results return in a
random order. If there is no caching, each request will return results in a
different order.

```
GET /api/v2/pages/?order=random

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 50
    },
    "items": [
        pages will be listed here in random order
    ]
}
```

```{note}
It's not possible to use `?offset` while ordering randomly because
consistent random ordering cannot be guaranteed over multiple requests
(so requests for subsequent pages may return results that also appeared in
previous pages).
```

### Filtering

Any field may be used in an exact match filter. Use the filter name as the
parameter and the value to match against.

For example, to find a page with the slug "about":

```
GET /api/v2/pages/?slug=about

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 1
    },
    "items": [
        {
            "id": 10,
            "meta": {
                "type": "standard.StandardPage",
                "detail_url": "http://api.example.com/api/v2/pages/10/",
                "html_url": "http://www.example.com/about/",
                "slug": "about",
                "first_published_at": "2016-08-30T16:52:00Z"
            },
            "title": "About"
        },
    ]
}
```

(apiv2_filter_by_tree_position)=

### Filtering by tree position (pages only)

Pages can additionally be filtered by their relation to other pages in the tree.

The `?child_of` filter takes the id of a page and filters the list of results
to contain only direct children of that page.

For example, this can be useful for constructing the main menu, by passing the
id of the homepage to the filter:

```
GET /api/v2/pages/?child_of=2&show_in_menus=true

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 5
    },
    "items": [
        {
            "id": 3,
            "meta": {
                "type": "blog.BlogIndexPage",
                "detail_url": "http://api.example.com/api/v2/pages/3/",
                "html_url": "http://www.example.com/blog/",
                "slug": "blog",
                "first_published_at": "2016-09-21T13:54:00Z"
            },
            "title": "About"
        },
        {
            "id": 10,
            "meta": {
                "type": "standard.StandardPage",
                "detail_url": "http://api.example.com/api/v2/pages/10/",
                "html_url": "http://www.example.com/about/",
                "slug": "about",
                "first_published_at": "2016-08-30T16:52:00Z"
            },
            "title": "About"
        },

        ...
    ]
}
```

The `?ancestor_of` filter takes the id of a page and filters the list
to only include ancestors of that page (parent, grandparent etc.) all the
way down to the site's root page.

For example, when combined with the `type` filter it can be used to
find the particular `blog.BlogIndexPage` a `blog.BlogPage` belongs
to. By itself, it can be used to to construct a breadcrumb trail from
the current page back to the site's root page.

The `?descendant_of` filter takes the id of a page and filter the list
to only include descendants of that page (children, grandchildren etc.).

(api_filtering_pages_by_site)=

### Filtering pages by site

```{versionadded} 4.0

```

By default, the API will look for the site based on the hostname of the request.
In some cases, you might want to query pages belonging to a different site.
The `?site=` filter is used to filter the listing to only include pages that
belong to a specific site. The filter requires the configured hostname of the
site. If you have multiple sites using the same hostname but a different port
number, it's possible to filter by port number using the format `hostname:port`.
For example:

```
GET /api/v2/pages/?site=demo-site.local
GET /api/v2/pages/?site=demo-site.local:8080
```

### Search

Passing a query to the `?search` parameter will perform a full-text search on
the results.

The query is split into "terms" (by word boundary), then each term is normalized
(lowercased and unaccented).

For example: `?search=James+Joyce`

#### Search operator

The `search_operator` specifies how multiple terms in the query should be
handled. There are two possible values:

-   `and` - All terms in the search query (excluding stop words) must exist in
    each result
-   `or` - At least one term in the search query must exist in each result

The `or` operator is generally better than `and` as it allows the user to be
inexact with their query and the ranking algorithm will make sure that
irrelevant results are not returned at the top of the page.

The default search operator depends on whether the search engine being used by
the site supports ranking. If it does (Elasticsearch), the operator will default
to `or`. Otherwise (database), it will default to `and`.

For the same reason, it's also recommended to use the `and` operator when
using `?search` in conjunction with `?order` (as this disables ranking).

For example: `?search=James+Joyce&order=-first_published_at&search_operator=and`

(apiv2_i18n_filters)=

### Special filters for internationalized sites

When `WAGTAIL_I18N_ENABLED` is set to `True` (see
[](enabling_internationalisation) for more details) two new filters are made
available on the pages endpoint.

#### Filtering pages by locale

The `?locale=` filter is used to filter the listing to only include pages in
the specified locale. For example:

```
GET /api/v2/pages/?locale=en-us

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 5
    },
    "items": [
        {
            "id": 10,
            "meta": {
                "type": "standard.StandardPage",
                "detail_url": "http://api.example.com/api/v2/pages/10/",
                "html_url": "http://www.example.com/usa-page/",
                "slug": "usa-page",
                "first_published_at": "2016-08-30T16:52:00Z",
                "locale": "en-us"
            },
            "title": "American page"
        },

        ...
    ]
}
```

#### Getting translations of a page

The `?translation_of` filter is used to filter the listing to only include
pages that are a translation of the specified page ID. For example:

```
GET /api/v2/pages/?translation_of=10

HTTP 200 OK
Content-Type: application/json

{
    "meta": {
        "total_count": 2
    },
    "items": [
        {
            "id": 11,
            "meta": {
                "type": "standard.StandardPage",
                "detail_url": "http://api.example.com/api/v2/pages/11/",
                "html_url": "http://www.example.com/gb-page/",
                "slug": "gb-page",
                "first_published_at": "2016-08-30T16:52:00Z",
                "locale": "en-gb"
            },
            "title": "British page"
        },
        {
            "id": 12,
            "meta": {
                "type": "standard.StandardPage",
                "detail_url": "http://api.example.com/api/v2/pages/12/",
                "html_url": "http://www.example.com/fr-page/",
                "slug": "fr-page",
                "first_published_at": "2016-08-30T16:52:00Z",
                "locale": "fr"
            },
            "title": "French page"
        },
    ]
}
```

### Fields

By default, only a subset of the available fields are returned in the response.
The `?fields` parameter can be used to both add additional fields to the
response and remove default fields that you know you won't need.

#### Additional fields

Additional fields can be added to the response by setting `?fields` to a
comma-separated list of field names you want to add.

For example, `?fields=body,feed_image` will add the `body` and `feed_image`
fields to the response.

This can also be used across relationships. For example,
`?fields=body,feed_image(width,height)` will nest the `width` and `height`
of the image in the response.

#### All fields

Setting `?fields` to an asterisk (`*`) will add all available fields to the
response. This is useful for discovering what fields have been exported.

For example: `?fields=*`

#### Removing fields

Fields you know that you do not need can be removed by prefixing the name with a
`-` and adding it to `?fields`.

For example, `?fields=-title,body` will remove `title` and add `body`.

This can also be used with the asterisk. For example, `?fields=*,-body`
adds all fields except for `body`.

#### Removing all default fields

To specify exactly the fields you need, you can set the first item in fields to
an underscore (`_`) which removes all default fields.

For example, `?fields=_,title` will only return the title field.

### Detail views

You can retrieve a single object from the API by appending its id to the end of
the URL. For example:

-   Pages `/api/v2/pages/1/`
-   Images `/api/v2/images/1/`
-   Documents `/api/v2/documents/1/`

All exported fields will be returned in the response by default. You can use the
`?fields` parameter to customize which fields are shown.

For example: `/api/v2/pages/1/?fields=_,title,body` will return just the
`title` and `body` of the page with the id of 1.

(apiv2_finding_pages_by_path)=

### Finding pages by HTML path

You can find an individual page by its HTML path using the `/api/v2/pages/find/?html_path=<path>` view.

This will return either a `302` redirect response to that page's detail view, or a `404` not found response.

For example: `/api/v2/pages/find/?html_path=/` always redirects to the homepage of the site

## Default endpoint fields

### Common fields

These fields are returned by every endpoint.

**`id` (number)**
The unique ID of the object

```{note}
Except for page types, every other content type has its own id space
so you must combine this with the ``type`` field in order to get a
unique identifier for an object.
```

**`type` (string)**
The type of the object in `app_label.ModelName` format

**`detail_url` (string)**
The URL of the detail view for the object

### Pages

**`title` (string)**
**`meta.slug` (string)**
**`meta.show_in_menus` (boolean)**
**`meta.seo_title` (string)**
**`meta.search_description` (string)**
**`meta.first_published_at` (date/time)**
These values are taken from their corresponding fields on the page

**`meta.html_url` (string)**
If the site has an HTML frontend that's generated by Wagtail, this
field will be set to the URL of this page

**`meta.parent`**
Nests some information about the parent page (only available on detail
views)

**`meta.alias_of` (dictionary)**
If the page marked as an alias return original page id and full url

### Images

**`title` (string)**
The value of the image's title field. Within Wagtail, this is used in
the image's `alt` HTML attribute.

**`width` (number)**
**`height` (number)**
The size of the original image file

**`meta.tags` (list of strings)**
A list of tags associated with the image

### Documents

**`title` (string)**
The value of the document's title field

**`meta.tags` (list of strings)**
A list of tags associated with the document

**`meta.download_url` (string)**
A URL to the document file

## Changes since v1

### Breaking changes

-   The results list in listing responses has been renamed to `items` (was previously either `pages`, `images` or `documents`)

### Major features

-   The `fields` parameter has been improved to allow removing fields, adding all fields and customising nested fields

### Minor features

-   `html_url`, `slug`, `first_published_at`, `expires_at` and `show_in_menus` fields have been added to the pages endpoint
-   `download_url` field has been added to the documents endpoint
-   Multiple page types can be specified in `type` parameter on pages endpoint
-   `true` and `false` may now be used when filtering boolean fields
-   `order` can now be used in conjunction with `search`
-   `search_operator` parameter was added
