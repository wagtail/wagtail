==============================
Configuring Django for Wagtail
==============================

To install Wagtail completely from scratch, create a new Django project and an app within that project. For instructions on these tasks, see `Writing your first Django app <https://docs.djangoproject.com/en/dev/intro/tutorial01/>`_. Your project directory will look like the following::

  myproject/
      myproject/
          __init__.py
          settings.py
          urls.py
          wsgi.py
      myapp/
          __init__.py
          models.py
          tests.py
          admin.py
          views.py
      manage.py

From your app directory, you can safely remove ``admin.py`` and ``views.py``, since Wagtail will provide this functionality for your models. Configuring Django to load Wagtail involves adding modules and variables to ``settings.py`` and URL configuration to ``urls.py``. For a more complete view of what's defined in these files, see `Django Settings <https://docs.djangoproject.com/en/dev/topics/settings/>`__ and `Django URL Dispatcher <https://docs.djangoproject.com/en/dev/topics/http/urls/>`_.

What follows is a settings reference which skips many boilerplate Django settings. If you just want to get your Wagtail install up quickly without fussing with settings at the moment, see :ref:`complete_example_config`.


Middleware (``settings.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',

    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
  ]

Wagtail requires several common Django middleware modules to work and cover basic security. Wagtail provides its own middleware to cover these tasks:

``SiteMiddleware``
  Wagtail routes pre-defined hosts to pages within the Wagtail tree using this middleware.

``RedirectMiddleware``
  Wagtail provides a simple interface for adding arbitrary redirects to your site and this module makes it happen.


Apps (``settings.py``)
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  INSTALLED_APPS = [

    'myapp',  # your own app

    'wagtail.wagtailforms',
    'wagtail.wagtailredirects',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsites',
    'wagtail.wagtailusers',
    'wagtail.wagtailsnippets',
    'wagtail.wagtaildocs',
    'wagtail.wagtailimages',
    'wagtail.wagtailsearch',
    'wagtail.wagtailadmin',
    'wagtail.wagtailcore',

    'taggit',
    'modelcluster',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
  ]

Wagtail requires several Django app modules, third-party apps, and defines several apps of its own. Wagtail was built to be modular, so many Wagtail apps can be omitted to suit your needs. Your own app (here ``myapp``) is where you define your models, templates, static assets, template tags, and other custom functionality for your site.


Wagtail Apps
------------

``wagtailcore``
  The core functionality of Wagtail, such as the ``Page`` class, the Wagtail tree, and model fields.

``wagtailadmin``
  The administration interface for Wagtail, including page edit handlers.

``wagtaildocs``
  The Wagtail document content type.

``wagtailsnippets``
  Editing interface for non-Page models and objects. See :ref:`Snippets`.

``wagtailusers``
  User editing interface.

``wagtailimages``
  The Wagtail image content type.

``wagtailembeds``
  Module governing oEmbed and Embedly content in Wagtail rich text fields. See :ref:`inserting_videos`.

``wagtailsearch``
  Search framework for Page content. See :ref:`search`.

``wagtailredirects``
  Admin interface for creating arbitrary redirects on your site.

``wagtailforms``
  Models for creating forms on your pages and viewing submissions. See :ref:`form_builder`.


Third-Party Apps
----------------

``taggit``
  Tagging framework for Django. This is used internally within Wagtail for image and document tagging and is available for your own models as well. See :ref:`tagging` for a Wagtail model recipe or the `Taggit Documentation`_.

.. _Taggit Documentation: http://django-taggit.readthedocs.org/en/latest/index.html

``modelcluster``
  Extension of Django ForeignKey relation functionality, which is used in Wagtail pages for on-the-fly related object creation. For more information, see :ref:`inline_panels` or `the django-modelcluster github project page`_.

.. _the django-modelcluster github project page: https://github.com/torchbox/django-modelcluster


Settings Variables (``settings.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Wagtail makes use of the following settings, in addition to `Django's core settings <https://docs.djangoproject.com/en/dev/ref/settings/>`__:


Site Name
---------

.. code-block:: python

  WAGTAIL_SITE_NAME = 'Stark Industries Skunkworks'

This is the human-readable name of your Wagtail install which welcomes users upon login to the Wagtail admin.


.. _append_slash:

Append Slash
------------

.. code-block:: python

  # Don't add a trailing slash to Wagtail-served URLs
  WAGTAIL_APPEND_SLASH = False

Similar to Django's ``APPEND_SLASH``, this setting controls how Wagtail will handle requests that don't end in a trailing slash.

When ``WAGTAIL_APPEND_SLASH`` is ``True`` (default), requests to Wagtail pages which omit a trailing slash will be redirected by Django's `CommonMiddleware`_ to a URL with a trailing slash.

When ``WAGTAIL_APPEND_SLASH`` is ``False``, requests to Wagtail pages will be served both with and without trailing slashes. Page links generated by Wagtail, however, will not include trailing slashes.

.. note::

  If you use the ``False`` setting, keep in mind that serving your pages both with and without slashes may affect search engines' ability to index your site. See `this Google Webmaster Blog post`_ for more details.

.. _commonmiddleware: https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.common
.. _this Google Webmaster Blog post: https://webmasters.googleblog.com/2010/04/to-slash-or-not-to-slash.html

Search
------

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch2',
          'INDEX': 'myapp'
      }
  }

Define a search backend. For a full explanation, see :ref:`wagtailsearch_backends`.

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE = 'myapp/search_results.html'
  WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX = 'myapp/includes/search_listing.html'

Override the templates used by the search front-end views.

.. _wagtailsearch_hits_max_age:

.. code-block:: python

  WAGTAILSEARCH_HITS_MAX_AGE = 14

Set the number of days (default 7) that search query logs are kept for; these are used to identify popular search terms for :ref:`promoted search results <editors-picks>`. Queries older than this will be removed by the :ref:`search_garbage_collect` command.


Embeds
------

Wagtail uses the oEmbed standard with a large but not comprehensive number of "providers" (Youtube, Vimeo, etc.). You can also use a different embed backend by providing an Embedly key or replacing the embed backend by writing your own embed finder function.

.. code-block:: python

  WAGTAILEMBEDS_EMBED_FINDER = 'myapp.embeds.my_embed_finder_function'

Use a custom embed finder function, which takes a URL and returns a dict with metadata and embeddable HTML. Refer to the ``wagtail.wagtailemebds.embeds`` module source for more information and examples.

.. code-block:: python

  # not a working key, get your own!
  WAGTAILEMBEDS_EMBEDLY_KEY = '253e433d59dc4d2xa266e9e0de0cb830'

Providing an API key for the Embedly service will use that as a embed backend, with a more extensive list of providers, as well as analytics and other features. For more information, see `Embedly`_.

.. _Embedly: http://embed.ly/

To use Embedly, you must also install their Python module:

.. code-block:: console

  $ pip install embedly


Dashboard
---------

.. versionadded:: 1.10

.. code-block:: python

    WAGTAILADMIN_RECENT_EDITS_LIMIT = 5

This setting lets you change the number of items shown at 'Your most recent edits' on the dashboard.


Images
------

.. code-block:: python

  WAGTAILIMAGES_IMAGE_MODEL = 'myapp.MyImage'

This setting lets you provide your own image model for use in Wagtail, which might extend the built-in ``AbstractImage`` class or replace it entirely.


Maximum Upload size for Images
------------------------------

.. code-block:: python

    WAGTAILIMAGES_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # i.e. 20MB

This setting lets you override the maximum upload size for images (in bytes). If omitted, Wagtail will fall back to using its 10MB default value.


Password Management
-------------------

.. code-block:: python

  WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = True

This specifies whether users are allowed to change their passwords (enabled by default).

.. code-block:: python

  WAGTAIL_PASSWORD_RESET_ENABLED = True

This specifies whether users are allowed to reset their passwords. Defaults to the same as ``WAGTAIL_PASSWORD_MANAGEMENT_ENABLED``.


Email Notifications
-------------------

.. code-block:: python

  WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'wagtail@myhost.io'

Wagtail sends email notifications when content is submitted for moderation, and when the content is accepted or rejected. This setting lets you pick which email address these automatic notifications will come from. If omitted, Django will fall back to using the ``DEFAULT_FROM_EMAIL`` variable if set, and ``webmaster@localhost`` if not.

.. _email_notifications_format:

Email Notifications format
--------------------------

.. code-block:: python

  WAGTAILADMIN_NOTIFICATION_USE_HTML = True

Notification emails are sent in `text/plain` by default, change this to use HTML formatting.


.. _update_notifications:

Wagtail update notifications
----------------------------

.. code-block:: python

  WAGTAIL_ENABLE_UPDATE_CHECK = True

For admins only, Wagtail performs a check on the dashboard to see if newer releases are available. This also provides the Wagtail team with the hostname of your Wagtail site. If you'd rather not receive update notifications, or if you'd like your site to remain unknown, you can disable it with this setting.


Private pages / documents
-------------------------

.. code-block:: python

  PASSWORD_REQUIRED_TEMPLATE = 'myapp/password_required.html'

This is the path to the Django template which will be used to display the "password required" form when a user accesses a private page. For more details, see the :ref:`private_pages` documentation.

.. code-block:: python

  DOCUMENT_PASSWORD_REQUIRED_TEMPLATE = 'myapp/document_password_required.html'

.. versionadded:: 1.11

As above, but for password restrictions on documents. For more details, see the :ref:`private_pages` documentation.

Case-Insensitive Tags
---------------------

.. code-block:: python

  TAGGIT_CASE_INSENSITIVE = True

Tags are case-sensitive by default ('music' and 'Music' are treated as distinct tags). In many cases the reverse behaviour is preferable.

Multi-word tags
---------------

.. versionadded:: 1.10

.. code-block:: python

  TAG_SPACES_ALLOWED = False

Tags can only consist of a single word, no spaces allowed. The default setting is ``True`` (spaces in tags are allowed).

Unicode Page Slugs
------------------

.. code-block:: python

  WAGTAIL_ALLOW_UNICODE_SLUGS = True

By default, page slugs can contain any alphanumeric characters, including non-Latin alphabets (except on Django 1.8, where only ASCII characters are supported). Set this to False to limit slugs to ASCII characters.

.. _WAGTAIL_AUTO_UPDATE_PREVIEW:

Auto update preview
-------------------

.. versionadded:: 1.10

.. code-block:: python

  WAGTAIL_AUTO_UPDATE_PREVIEW = False

When enabled, data from an edited page is automatically sent to the server
on each change, even without saving. That way, users don’t have to click on
“Preview” to update the content of the preview page. However, the preview page
tab is not refreshed automatically, users have to do it manually.
This behaviour is disabled by default.

Custom User Edit Forms
----------------------

See :doc:`/advanced_topics/customisation/custom_user_models`.

.. code-block:: python

  WAGTAIL_USER_EDIT_FORM = 'users.forms.CustomUserEditForm'

Allows the default ``UserEditForm`` class to be overridden with a custom form when
a custom user model is being used and extra fields are required in the user edit form.

.. code-block:: python

  WAGTAIL_USER_CREATION_FORM = 'users.forms.CustomUserCreationForm'

Allows the default ``UserCreationForm`` class to be overridden with a custom form when
a custom user model is being used and extra fields are required in the user creation form.

.. code-block:: python

  WAGTAIL_USER_CUSTOM_FIELDS = ['country']

A list of the extra custom fields to be appended to the default list.

Usage for images, documents and snippets
----------------------------------------

.. code-block:: python

    WAGTAIL_USAGE_COUNT_ENABLED = True

When enabled Wagtail shows where a particular image, document or snippet is being used on your site (disabled by default). A link will appear on the edit page showing you which pages they have been used on.

.. note::

    The usage count only applies to direct (database) references. Using documents, images and snippets within StreamFields or rich text fields will not be taken into account.

Date and DateTime inputs
------------------------

.. code-block:: python

    WAGTAIL_DATE_FORMAT = '%d.%m.%Y.'
    WAGTAIL_DATETIME_FORMAT = '%d.%m.%Y. %H:%M'


Specifies the date and datetime format to be used in input fields in the Wagtail admin. The format is specified in `Python datetime module syntax <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_, and must be one of the recognised formats listed in the ``DATE_INPUT_FORMATS`` or ``DATETIME_INPUT_FORMATS`` setting respectively (see `DATE_INPUT_FORMATS <https://docs.djangoproject.com/en/1.10/ref/settings/#std:setting-DATE_INPUT_FORMATS>`_).

.. _WAGTAILADMIN_PERMITTED_LANGUAGES:

Admin languages
---------------

.. versionadded:: 1.10

Users can choose between several languages for the admin interface
in the account settings. The list of languages is by default all the available
languages in Wagtail. To change it, set ``WAGTAILADMIN_PERMITTED_LANGUAGES``:

.. code-block:: python

    WAGTAILADMIN_PERMITTED_LANGUAGES = [('en', 'English'),
                                        ('pt', 'Portuguese')]

Since the syntax is the same as Django ``LANGUAGES``, you can do this so users
can only choose between front office languages:

.. code-block:: python

    LANGUAGES = WAGTAILADMIN_PERMITTED_LANGUAGES = [('en', 'English'),
                                                    ('pt', 'Portuguese')]


URL Patterns
~~~~~~~~~~~~

.. code-block:: python

  from django.contrib import admin

  from wagtail.wagtailcore import urls as wagtail_urls
  from wagtail.wagtailadmin import urls as wagtailadmin_urls
  from wagtail.wagtaildocs import urls as wagtaildocs_urls
  from wagtail.wagtailsearch import urls as wagtailsearch_urls

  urlpatterns = [
      url(r'^django-admin/', include(admin.site.urls)),

      url(r'^admin/', include(wagtailadmin_urls)),
      url(r'^search/', include(wagtailsearch_urls)),
      url(r'^documents/', include(wagtaildocs_urls)),

      # Optional URL for including your own vanilla Django urls/views
      url(r'', include('myapp.urls')),

      # For anything not caught by a more specific rule above, hand over to
      # Wagtail's serving mechanism
      url(r'', include(wagtail_urls)),
  ]

This block of code for your project's ``urls.py`` does a few things:

* Load the vanilla Django admin interface to ``/django-admin/``
* Load the Wagtail admin and its various apps
* Dispatch any vanilla Django apps you're using other than Wagtail which require their own URL configuration (this is optional, since Wagtail might be all you need)
* Lets Wagtail handle any further URL dispatching.

That's not everything you might want to include in your project's URL configuration, but it's what's necessary for Wagtail to flourish.


.. _complete_example_config:

Ready to Use Example Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These two files should reside in your project directory (``myproject/myproject/``).


``settings.py``
---------------

.. code-block:: python

  import os

  PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  BASE_DIR = os.path.dirname(PROJECT_DIR)

  DEBUG = True

  # Application definition

  INSTALLED_APPS = [
      'myapp',

      'wagtail.wagtailforms',
      'wagtail.wagtailredirects',
      'wagtail.wagtailembeds',
      'wagtail.wagtailsites',
      'wagtail.wagtailusers',
      'wagtail.wagtailsnippets',
      'wagtail.wagtaildocs',
      'wagtail.wagtailimages',
      'wagtail.wagtailsearch',
      'wagtail.wagtailadmin',
      'wagtail.wagtailcore',

      'taggit',
      'modelcluster',

      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',
  ]


  MIDDLEWARE_CLASSES = [
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.middleware.common.CommonMiddleware',
      'django.middleware.csrf.CsrfViewMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'django.middleware.clickjacking.XFrameOptionsMiddleware',
      'django.middleware.security.SecurityMiddleware',

      'wagtail.wagtailcore.middleware.SiteMiddleware',
      'wagtail.wagtailredirects.middleware.RedirectMiddleware',
  ]

  ROOT_URLCONF = 'myproject.urls'

  TEMPLATES = [
      {
          'BACKEND': 'django.template.backends.django.DjangoTemplates',
          'DIRS': [
              os.path.join(PROJECT_DIR, 'templates'),
          ],
          'APP_DIRS': True,
          'OPTIONS': {
              'context_processors': [
                  'django.template.context_processors.debug',
                  'django.template.context_processors.request',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages',
              ],
          },
      },
  ]

  WSGI_APPLICATION = 'wagtaildemo.wsgi.application'

  # Database

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql_psycopg2',
          'NAME': 'myprojectdb',
          'USER': 'postgres',
          'PASSWORD': '',
          'HOST': '',  # Set to empty string for localhost.
          'PORT': '',  # Set to empty string for default.
          'CONN_MAX_AGE': 600,  # number of seconds database connections should persist for
      }
  }

  # Internationalization

  LANGUAGE_CODE = 'en-us'
  TIME_ZONE = 'UTC'
  USE_I18N = True
  USE_L10N = True
  USE_TZ = True


  # Static files (CSS, JavaScript, Images)

  STATICFILES_FINDERS = [
      'django.contrib.staticfiles.finders.FileSystemFinder',
      'django.contrib.staticfiles.finders.AppDirectoriesFinder',
  ]

  STATICFILES_DIRS = [
      os.path.join(PROJECT_DIR, 'static'),
  ]

  STATIC_ROOT = os.path.join(BASE_DIR, 'static')
  STATIC_URL = '/static/'

  MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
  MEDIA_URL = '/media/'


  ADMINS = [
      # ('Your Name', 'your_email@example.com'),
  ]
  MANAGERS = ADMINS

  # Default to dummy email backend. Configure dev/production/local backend
  # as per https://docs.djangoproject.com/en/dev/topics/email/#email-backends
  EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

  # Hosts/domain names that are valid for this site; required if DEBUG is False
  ALLOWED_HOSTS = []

  # Make this unique, and don't share it with anybody.
  SECRET_KEY = 'change-me'

  EMAIL_SUBJECT_PREFIX = '[Wagtail] '

  INTERNAL_IPS = ('127.0.0.1', '10.0.2.2')

  # A sample logging configuration. The only tangible logging
  # performed by this configuration is to send an email to
  # the site admins on every HTTP 500 error when DEBUG=False.
  # See http://docs.djangoproject.com/en/dev/topics/logging for
  # more details on how to customize your logging configuration.
  LOGGING = {
      'version': 1,
      'disable_existing_loggers': False,
      'filters': {
          'require_debug_false': {
              '()': 'django.utils.log.RequireDebugFalse'
          }
      },
      'handlers': {
          'mail_admins': {
              'level': 'ERROR',
              'filters': ['require_debug_false'],
              'class': 'django.utils.log.AdminEmailHandler'
          }
      },
      'loggers': {
          'django.request': {
              'handlers': ['mail_admins'],
              'level': 'ERROR',
              'propagate': True,
          },
      }
  }


  # WAGTAIL SETTINGS

  # This is the human-readable name of your Wagtail install
  # which welcomes users upon login to the Wagtail admin.
  WAGTAIL_SITE_NAME = 'My Project'

  # Override the search results template for wagtailsearch
  # WAGTAILSEARCH_RESULTS_TEMPLATE = 'myapp/search_results.html'
  # WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX = 'myapp/includes/search_listing.html'

  # Replace the search backend
  #WAGTAILSEARCH_BACKENDS = {
  #  'default': {
  #    'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch2',
  #    'INDEX': 'myapp'
  #  }
  #}

  # Wagtail email notifications from address
  # WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'wagtail@myhost.io'

  # Wagtail email notification format
  # WAGTAILADMIN_NOTIFICATION_USE_HTML = True

  # If you want to use Embedly for embeds, supply a key
  # (this key doesn't work, get your own!)
  # WAGTAILEMBEDS_EMBEDLY_KEY = '253e433d59dc4d2xa266e9e0de0cb830'

  # Reverse the default case-sensitive handling of tags
  TAGGIT_CASE_INSENSITIVE = True


``urls.py``
-----------

.. code-block:: python

  from django.conf.urls import include, url
  from django.conf.urls.static import static
  from django.views.generic.base import RedirectView
  from django.contrib import admin
  from django.conf import settings
  import os.path

  from wagtail.wagtailcore import urls as wagtail_urls
  from wagtail.wagtailadmin import urls as wagtailadmin_urls
  from wagtail.wagtaildocs import urls as wagtaildocs_urls
  from wagtail.wagtailsearch import urls as wagtailsearch_urls


  urlpatterns = [
      url(r'^django-admin/', include(admin.site.urls)),

      url(r'^admin/', include(wagtailadmin_urls)),
      url(r'^search/', include(wagtailsearch_urls)),
      url(r'^documents/', include(wagtaildocs_urls)),

      # For anything not caught by a more specific rule above, hand over to
      # Wagtail's serving mechanism
      url(r'', include(wagtail_urls)),
  ]


  if settings.DEBUG:
      from django.contrib.staticfiles.urls import staticfiles_urlpatterns

      urlpatterns += staticfiles_urlpatterns() # tell gunicorn where static files are in dev mode
      urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
      urlpatterns += [
          url(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'myapp/images/favicon.ico'))
      ]
