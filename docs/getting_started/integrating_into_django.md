# Integrating Wagtail into a Django project

Wagtail provides the `wagtail start` command and project template to get you started with a new Wagtail project as quickly as possible, but it's easy to integrate Wagtail into an existing Django project too.

Wagtail is currently compatible with Django 3.2, 4.1, and 4.2. First, install the `wagtail` package from PyPI:

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

Add a `STATIC_ROOT` setting, if your project doesn't have one already:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```

Add `MEDIA_ROOT` and `MEDIA_URL` settings, if your project doesn't have these already:

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

Note that this only works in development mode (`DEBUG = True`); in production, you have to configure your web server to serve files from `MEDIA_ROOT`. For further details, see the Django documentation: [Serving files uploaded by a user during development](https://docs.djangoproject.com/en/stable/howto/static-files/#serving-files-uploaded-by-a-user-during-development) and [Deploying static files](django:howto/static-files/deployment).

With this configuration in place, you are ready to run `python manage.py migrate` to create the database tables used by Wagtail.

## User accounts

Wagtail uses Django’s default user model by default. Superuser accounts receive automatic access to the Wagtail [admin interface](https://guide.wagtail.org/en-latest/concepts/wagtail-interfaces/#admin-interface); use `python manage.py createsuperuser` if you don't already have one. Wagtail supports custom user models with some restrictions. Wagtail uses an extension of Django's permissions framework, so your user model must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`.

## Start developing

You're now ready to add a new app to your Django project through `python manage.py startapp`. Remember to add the new app to `INSTALLED_APPS` in your settings.py file and set up page models, as described in [Your first Wagtail site](/getting_started/tutorial).

Note that there's one small difference when you're not using the Wagtail project template: Wagtail creates an initial homepage of the basic type `Page`, which doesn't include any content fields beyond the title. You probably want to replace this with your own `HomePage` class. If you do so, ensure that you set up a site record (under Settings / Sites in the Wagtail admin) to point to the new homepage.
