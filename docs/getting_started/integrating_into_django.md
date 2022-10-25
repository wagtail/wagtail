# Integrating Wagtail into a Django project

Wagtail provides the `wagtail start` command and project template to get you started with a new Wagtail project as quickly as possible, but it's easy to integrate Wagtail into an existing Django project too.

Wagtail is currently compatible with Django 3.2, 4.0, and 4.1. First, install the `wagtail` package from PyPI:

```sh
pip install wagtail
```

or add the package to your existing requirements file. This will also install the **Pillow** library as a dependency, which requires libjpeg and zlib - see Pillow's [platform-specific installation instructions](https://pillow.readthedocs.io/en/stable/installation.html#external-libraries).

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

Add a `STATIC_ROOT` setting, if your project does not have one already:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```

Add `MEDIA_ROOT` and `MEDIA_URL` settings, if your project does not have these already:

```python
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
```

Add a `WAGTAIL_SITE_NAME` - this will be displayed on the main dashboard of the Wagtail admin backend:

```python
WAGTAIL_SITE_NAME = 'My Example Site'
```

Various other settings are available to configure Wagtail's behaviour - see [Settings](/reference/settings).

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

The URL paths here can be altered as necessary to fit your project's URL scheme.

`wagtailadmin_urls` provides the admin interface for Wagtail. This is separate from the Django admin interface (`django.contrib.admin`); Wagtail-only projects typically host the Wagtail admin at `/admin/`, but if this would clash with your project's existing admin backend then an alternative path can be used, such as `/cms/` here.

`wagtaildocs_urls` is the location from where document files will be served. This can be omitted if you do not intend to use Wagtail's document management features.

`wagtail_urls` is the base location from where the pages of your Wagtail site will be served. In the above example, Wagtail will handle URLs under `/pages/`, leaving the root URL and other paths to be handled as normal by your Django project. If you want Wagtail to handle the entire URL space including the root URL, this can be replaced with:

```python
path('', include(wagtail_urls)),
```

In this case, this should be placed at the end of the `urlpatterns` list, so that it does not override more specific URL patterns.

Finally, your project needs to be set up to serve user-uploaded files from `MEDIA_ROOT`. Your Django project may already have this in place, but if not, add the following snippet to `urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... the rest of your URLconf goes here ...
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Note that this only works in development mode (`DEBUG = True`); in production, you will need to configure your web server to serve files from `MEDIA_ROOT`. For further details, see the Django documentation: [Serving files uploaded by a user during development](https://docs.djangoproject.com/en/stable/howto/static-files/#serving-files-uploaded-by-a-user-during-development) and [Deploying static files](https://docs.djangoproject.com/en/stable/howto/static-files/deployment/).

With this configuration in place, you are ready to run `python manage.py migrate` to create the database tables used by Wagtail.

## User accounts

Superuser accounts receive automatic access to the Wagtail admin interface; use `python manage.py createsuperuser` if you don't already have one. Custom user models are supported, with some restrictions; Wagtail uses an extension of Django's permissions framework, so your user model must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`.

## Start developing

You're now ready to add a new app to your Django project (via `python manage.py startapp` - remember to add it to `INSTALLED_APPS` in your settings.py file) and set up page models, as described in [Your first Wagtail site](/getting_started/tutorial).

Note that there's one small difference when not using the Wagtail project template: Wagtail creates an initial homepage of the basic type `Page`, which does not include any content fields beyond the title. You'll probably want to replace this with your own `HomePage` class - when you do so, ensure that you set up a site record (under Settings / Sites in the Wagtail admin) to point to the new homepage.
