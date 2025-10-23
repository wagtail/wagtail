# Integrating Wagtail into a Django project

Wagtail provides the `wagtail start` command and project template to get you started with a new Wagtail project as quickly as possible, but it's easy to integrate Wagtail into an existing Django project too.

```{note}
We highly recommend working through the [Getting Started tutorial](tutorial), even if you are not planning to create a standalone Wagtail project. This will ensure you have a good understanding of Wagtail concepts.
```

Wagtail is currently compatible with Django 4.2, 5.1 and 5.2. First, install the `wagtail` package from PyPI:

```sh
pip install wagtail
```

or add the package to your existing requirements file. This will also install the **Pillow** library as a dependency, which requires libjpeg and zlib - see Pillow's [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation/building-from-source.html#external-libraries).

## Settings

In your settings.py file, add the following apps to `INSTALLED_APPS`:

```python
'wagtail.contrib.forms',
'wagtail.contrib.redirects',
'wagtail.embeds',
'wagtail.sites',
'wagtail.users',
'wagtail.snippets',
'wagtail.documents',
'wagtail.images',
'wagtail.search',
'wagtail.admin',
'wagtail',

'modelcluster',
'taggit',
```

Add the following entry to `MIDDLEWARE`:

```python
'wagtail.contrib.redirects.middleware.RedirectMiddleware',
```

Add a `STATIC_ROOT` setting, if your project doesn't have one already:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```

Add `MEDIA_ROOT` and `MEDIA_URL` settings, if your project doesn't have these already:

```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

Set the `DATA_UPLOAD_MAX_NUMBER_FIELDS` setting to 10000 or higher. This specifies the maximum number of fields allowed in a form submission, and it is recommended to increase this from Django's default of 1000, as particularly complex page models can exceed this limit within Wagtail's page editor:

```python
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000
```

Add a `WAGTAIL_SITE_NAME` - this will be displayed on the main dashboard of the Wagtail admin backend:

```python
WAGTAIL_SITE_NAME = 'My Example Site'
```

Add a `WAGTAILADMIN_BASE_URL` - this is the base URL used by the Wagtail admin site. It is typically used for generating URLs to include in notification emails:

```python
WAGTAILADMIN_BASE_URL = 'http://example.com'
```

If this setting is not present, Wagtail will fall back to `request.site.root_url` or to the hostname of the request. Although this setting is not strictly required, it is highly recommended because leaving it out may produce unusable URLs in notification emails.

Add a `WAGTAILDOCS_EXTENSIONS` setting to specify the file types that Wagtail will allow to be uploaded as documents. This can be omitted to allow all file types, but this may present a security risk if untrusted users are allowed to upload documents - see [](user_uploaded_files).

```python
WAGTAILDOCS_EXTENSIONS = ['csv', 'docx', 'key', 'odt', 'pdf', 'pptx', 'rtf', 'txt', 'xlsx', 'zip']
```

Various other settings are available to configure Wagtail's behavior - see [Settings](/reference/settings).

## URL configuration

Now make the following additions to your `urls.py` file:

```python
from django.urls import path, include

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    ...
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('pages/', include(wagtail_urls)),
    ...
]
```

You can alter URL paths here to fit your project's URL scheme.

`wagtailadmin_urls` provides the [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface) for Wagtail. This is separate from the Django admin interface, `django.contrib.admin`. Wagtail-only projects host the Wagtail admin at `/admin/`, but if this clashes with your project's existing admin backend then you can use an alternative path, such as `/cms/`.

Wagtail serves your document files from the location, `wagtaildocs_urls`. You can omit this if you do not intend to use Wagtail's document management features.

Wagtail serves your pages from the `wagtail_urls` location. In the above example, Wagtail handles URLs under `/pages/`, leaving your Django project to handle the root URL and other paths as normal. If you want Wagtail to handle the entire URL space including the root URL, then place `path('', include(wagtail_urls))` at the end of the `urlpatterns` list. Placing `path('', include(wagtail_urls))` at the end of the `urlpatterns` ensures that it doesn't override more specific URL patterns.

Finally, you need to set up your project to serve user-uploaded files from `MEDIA_ROOT`. Your Django project may already have this in place, but if not, add the following snippet to `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... the rest of your URLconf goes here ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Note that this only works in development mode (`DEBUG = True`); in production, you have to configure your web server to serve files from `MEDIA_ROOT`. For further details, see the Django documentation: [Serving files uploaded by a user during development](<inv:django#howto/static-files/index:serving files uploaded by a user during development>) and [Deploying static files](inv:django#howto/static-files/deployment).

With this configuration in place, you are ready to run `python manage.py migrate` to create the database tables used by Wagtail.

## User accounts

Wagtail uses Django’s default user model by default. Superuser accounts receive automatic access to the Wagtail [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface); use `python manage.py createsuperuser` if you don't already have one. Wagtail supports custom user models with some restrictions. Wagtail uses an extension of Django's permissions framework, so your user model must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`.

## Define page models and start developing

Before you can create pages, you must define one or more page models, as described in [Your first Wagtail site](/getting_started/tutorial). The `wagtail start` project template provides a `home` app containing an initial `HomePage` model - when integrating Wagtail into an existing project, you will need to create this app yourself through `python manage.py startapp`. (Remember to add it to `INSTALLED_APPS` in your settings.py file.)

The initial "Welcome to your new Wagtail site!" page is a placeholder using the base `Page` model, and is not directly usable. After defining your own home page model, you should create a new page at the root level through the Wagtail admin interface, and set this as the site's homepage (under Settings / Sites). You can then delete the placeholder page.
