(redirects)=

# Redirects

```{eval-rst}
.. module:: wagtail.contrib.redirects
```

The `redirects` module provides the models and user interface for managing arbitrary redirection between urls and `Pages` or other urls.

## Installation

The `redirects` module is not enabled by default. To install it, add `wagtail.contrib.redirects` to `INSTALLED_APPS` and `wagtail.contrib.redirects.middleware.RedirectMiddleware` to `MIDDLEWARE` in your project's Django settings file.

```python
INSTALLED_APPS = [
    # ...

    'wagtail.contrib.redirects',
]

MIDDLEWARE = [
    # ...
    # all other django middlware first

    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
]
```

This app contains migrations so make sure you run the `migrate` django-admin command after installing.

## Usage

Once installed, a new menu item called "Redirects" should appear in the "Settings" menu. This is where you can add arbitrary redirects to your site.

For an editor's guide to the interface, see [](managing_redirects).

## Automatic redirect creation

```{versionadded} 2.16

```

Wagtail automatically creates permanent redirects for pages (and their descendants) when they are moved or their slug is changed. This helps to preserve SEO rankings of pages over time, and helps site visitors get to the right place when using bookmarks or using outdated links.

### Creating redirects for alternative page routes

If your project uses `RoutablePageMixin` to create pages with alternative routes, you might want to consider overriding the `get_route_paths()` method for those page types. Adding popular route paths to this list will result in the creation of additional redirects; helping visitors to alternative routes to get to the right place also.

For more information, please see :meth:`~wagtail.models.Page.get_route_paths`.

### Disabling automatic redirect creation

```{versionadded} 4.0
When generating redirects, custom field values are now fetched as part of the
initial database query, so using custom field values in overridden url methods
will no longer trigger additional per-object queries.
```

Wagtail's default implementation works best for small-to-medium sized projects (5000 pages or fewer) that mostly use Wagtail's built-in methods for URL generation.

Overrides to the following `Page` methods are respected when generating redirects, but use of specific page fields in those overrides will trigger additional database queries.

-   {meth}`~wagtail.models.Page.get_url_parts()`
-   {meth}`~wagtail.models.Page.get_route_paths()`

If you find the feature is not a good fit for your project, you can disable it by adding the following to your project settings:

```python
WAGTAILREDIRECTS_AUTO_CREATE = False
```

## Management commands

### `import_redirects`

```console
$ ./manage.py import_redirects
```

This command imports and creates redirects from a file supplied by the user.

Options:

| Option        | Description                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------------- |
| **src**       | This is the path to the file you wish to import redirects from.                                |
| **site**      | This is the **site** for the site you wish to save redirects to.                               |
| **permanent** | If the redirects imported should be **permanent** (True) or not (False). It's True by default. |
| **from**      | The column index you want to use as redirect from value.                                       |
| **to**        | The column index you want to use as redirect to value.                                         |
| **dry_run**   | Lets you run a import without doing any changes.                                               |
| **ask**       | Lets you inspect and approve each redirect before it is created.                               |

## The `Redirect` class

```{eval-rst}
.. automodule:: wagtail.contrib.redirects.models
```

```{eval-rst}
.. autoclass:: Redirect

    .. automethod:: add_redirect
```
