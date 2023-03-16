Integrating Wagtail into a Django Project
Wagtail provides a wagtail start command and project template to get started with a new Wagtail project quickly, but it's also easy to integrate Wagtail into an existing Django project.

To use Wagtail in your Django project, ensure you have Django 3.2, 4.0, or 4.1 installed, then install the wagtail package from PyPI using the command:

Copy code
pip install wagtail
This will also install the Pillow library as a dependency, which requires libjpeg and zlib. See Pillow's platform-specific installation instructions for more information.

Settings
In your settings.py file, add the following apps to INSTALLED_APPS:

python
Copy code
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
Add the following entry to MIDDLEWARE:

python
Copy code
'wagtail.contrib.redirects.middleware.RedirectMiddleware',
If your project doesn't already have a STATIC_ROOT setting, add the following to your settings.py file:

lua
Copy code
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
Add the following settings to settings.py if they are not already present:

lua
Copy code
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
To set the name of your site, add the following setting to settings.py:

python
Copy code
WAGTAIL_SITE_NAME = 'My Example Site'
There are other settings available to configure Wagtail's behavior - see the Wagtail documentation for more information.

URL Configuration
Add the following to your urls.py file:

python
Copy code
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
The URL paths can be altered as necessary to fit your project's URL scheme.

wagtailadmin_urls provides the admin interface for Wagtail, which is separate from the Django admin interface (django.contrib.admin). If the Wagtail admin URL clashes with your project's existing admin backend, then an alternative path can be used. For example, /cms/ here.

wagtaildocs_urls is where document files will be served. You can omit this if you don't plan to use Wagtail's document management features.

wagtail_urls is the base location where the pages of your Wagtail site will be served. In the example above, Wagtail handles URLs under /pages/, leaving the root URL and other paths to be handled normally by your Django project. If you want Wagtail to handle the entire URL space, including the root URL, replace the wagtail_urls line with the following:

less
Copy code
path('', include(wagtail_urls)),
Place this at the end of the urlpatterns list to avoid overriding more specific URL patterns.

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

Wagtail uses Django’s default user model by default. Superuser accounts receive automatic access to the Wagtail admin interface; use `python manage.py createsuperuser` if you don't already have one. Custom user models are supported, with some restrictions; Wagtail uses an extension of Django's permissions framework, so your user model must at minimum inherit from `AbstractBaseUser` and `PermissionsMixin`.

## Start developing

You're now ready to add a new app to your Django project (via `python manage.py startapp` - remember to add it to `INSTALLED_APPS` in your settings.py file) and set up page models, as described in [Your first Wagtail site](/getting_started/tutorial).

Note that there's one small difference when not using the Wagtail project template: Wagtail creates an initial homepage of the basic type `Page`, which does not include any content fields beyond the title. You'll probably want to replace this with your own `HomePage` class - when you do so, ensure that you set up a site record (under Settings / Sites in the Wagtail admin) to point to the new homepage.
