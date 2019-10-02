==============================
Configuring Django for Wagtail
==============================

To install Wagtail completely from scratch, create a new Django project and an app within that project. For instructions on these tasks, see :doc:`Writing your first Django app <django:intro/tutorial01>`. Your project directory will look like the following::

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

From your app directory, you can safely remove ``admin.py`` and ``views.py``, since Wagtail will provide this functionality for your models. Configuring Django to load Wagtail involves adding modules and variables to ``settings.py`` and URL configuration to ``urls.py``. For a more complete view of what's defined in these files, see :doc:`Django Settings <django:topics/settings>` and :doc:`Django URL Dispatcher <django:topics/http/urls>`.

What follows is a settings reference which skips many boilerplate Django settings. If you just want to get your Wagtail install up quickly without fussing with settings at the moment, see :ref:`complete_example_config`.


Middleware (``settings.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

  MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'wagtail.core.middleware.SiteMiddleware',

    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
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
    'wagtail.core',

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
  Search framework for Page content. See :ref:`wagtailsearch`.

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

Wagtail makes use of the following settings, in addition to :doc:`Django's core settings <ref/settings>`:


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

When ``WAGTAIL_APPEND_SLASH`` is ``True`` (default), requests to Wagtail pages which omit a trailing slash will be redirected by Django's :class:`~django.middleware.common.CommonMiddleware` to a URL with a trailing slash.

When ``WAGTAIL_APPEND_SLASH`` is ``False``, requests to Wagtail pages will be served both with and without trailing slashes. Page links generated by Wagtail, however, will not include trailing slashes.

.. note::

  If you use the ``False`` setting, keep in mind that serving your pages both with and without slashes may affect search engines' ability to index your site. See `this Google Webmaster Blog post`_ for more details.

.. _this Google Webmaster Blog post: https://webmasters.googleblog.com/2010/04/to-slash-or-not-to-slash.html

Search
------

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.search.backends.elasticsearch2',
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

Wagtail supports generating embed code from URLs to content on an external
providers such as Youtube or Twitter. By default, Wagtail will fetch the embed
code directly from the relevant provider's site using the oEmbed protocol.
Wagtail has a builtin list of the most common providers.

The embeds fetching can be fully configured using the ``WAGTAILEMBEDS_FINDERS``
setting. This is fully documented in :ref:`configuring_embed_finders`.


Dashboard
---------

.. code-block:: python

    WAGTAILADMIN_RECENT_EDITS_LIMIT = 5

This setting lets you change the number of items shown at 'Your most recent edits' on the dashboard.


.. code-block:: python

  WAGTAILADMIN_USER_LOGIN_FORM = 'users.forms.LoginForm'

Allows the default ``LoginForm`` to be extended with extra fields.


.. _wagtail_gravatar_provider_url:

.. code-block:: python

  WAGTAIL_GRAVATAR_PROVIDER_URL = '//www.gravatar.com/avatar'

If a user has not uploaded a profile picture, Wagtail will look for an avatar linked to their email address on gravatar.com. This setting allows you to specify an alternative provider such as like robohash.org, or can be set to ``None`` to disable the use of remote avatars completely.

.. _wagtail_moderation_enabled:

.. code-block:: python

  WAGTAIL_MODERATION_ENABLED = True

Changes whether the Submit for Moderation button is displayed in the action menu.



Images
------

.. code-block:: python

  WAGTAILIMAGES_IMAGE_MODEL = 'myapp.MyImage'

This setting lets you provide your own image model for use in Wagtail, which might extend the built-in ``AbstractImage`` class or replace it entirely.


.. code-block:: python

    WAGTAILIMAGES_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # i.e. 20MB

This setting lets you override the maximum upload size for images (in bytes). If omitted, Wagtail will fall back to using its 10MB default value.

.. code-block:: python

    WAGTAILIMAGES_MAX_IMAGE_PIXELS = 128000000  # i.e. 128 megapixels

This setting lets you override the maximum number of pixels an image can have. If omitted, Wagtail will fall back to using its 128 megapixels default value.

.. code-block:: python

    WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True

This setting enables feature detection once OpenCV is installed, see all details on the :ref:`image_feature_detection` documentation.

.. code-block:: python

    WAGTAILIMAGES_INDEX_PAGE_SIZE = 20

Specifies the number of images per page shown on the main Images listing in the Wagtail admin.

.. code-block:: python

    WAGTAILIMAGES_USAGE_PAGE_SIZE = 20

Specifies the number of items per page shown when viewing an image's usage (see :ref:`WAGTAIL_USAGE_COUNT_ENABLED <WAGTAIL_USAGE_COUNT_ENABLED>`).

.. code-block:: python

    WAGTAILIMAGES_CHOOSER_PAGE_SIZE = 12

Specifies the number of images shown per page in the image chooser modal.


Documents
---------

.. _wagtaildocs_serve_method:

.. code-block:: python

  WAGTAILDOCS_SERVE_METHOD = 'redirect'

Determines how document downloads will be linked to and served. Normally, requests for documents are sent through a Django view, to perform permission checks (see :ref:`image_document_permissions`) and potentially other housekeeping tasks such as hit counting. To fully protect against users bypassing this check, it needs to happen in the same request where the document is served; however, this incurs a performance hit as the document then needs to be served by the Django server. In particular, this cancels out much of the benefit of hosting documents on external storage, such as S3 or a CDN.

For this reason, Wagtail provides a number of serving methods which trade some of the strictness of the permission check for performance:

 * ``'direct'`` - links to documents point directly to the URL provided by the underlying storage, bypassing the Django view that provides the permission check. This is most useful when deploying sites as fully static HTML (e.g. using `wagtail-bakery <https://github.com/wagtail/wagtail-bakery>`_ or `Gatsby <https://www.gatsbyjs.org/>`_).
 * ``'redirect'`` - links to documents point to a Django view which will check the user's permission; if successful, it will redirect to the URL provided by the underlying storage to allow the document to be downloaded. This is most suitable for remote storage backends such as S3, as it allows the document to be served independently of the Django server. Note that if a user is able to guess the latter URL, they will be able to bypass the permission check; some storage backends may provide configuration options to generate a random or short-lived URL to mitigate this.
 * ``'serve_view'`` - links to documents point to a Django view which both checks the user's permission, and serves the document. Serving will be handled by `django-sendfile <https://github.com/johnsensible/django-sendfile>`_, if this is installed and supported by your server configuration, or as a streaming response from Django if not. When using this method, it is recommended that you configure your webserver to *disallow* serving documents directly from their location under ``MEDIA_ROOT``, as this would provide a way to bypass the permission check.

If ``WAGTAILDOCS_SERVE_METHOD`` is unspecified or set to ``None``, the default method is ``'redirect'`` when a remote storage backend is in use (i.e. one that exposes a URL but not a local filesystem path), and ``'serve_view'`` otherwise. Finally, some storage backends may not expose a URL at all; in this case, serving will proceed as for ``'serve_view'``.


Password Management
-------------------

.. code-block:: python

  WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = True

This specifies whether users are allowed to change their passwords (enabled by default).

.. code-block:: python

  WAGTAIL_PASSWORD_RESET_ENABLED = True

This specifies whether users are allowed to reset their passwords. Defaults to the same as ``WAGTAIL_PASSWORD_MANAGEMENT_ENABLED``.

.. code-block:: python

  WAGTAILUSERS_PASSWORD_ENABLED = True

This specifies whether password fields are shown when creating or editing users through Settings -> Users (enabled by default). Set this to False (along with ``WAGTAIL_PASSWORD_MANAGEMENT_ENABLED`` and ``WAGTAIL_PASSWORD_RESET_ENABLED``) if your users are authenticated through an external system such as LDAP.

.. code-block:: python

  WAGTAILUSERS_PASSWORD_REQUIRED = True

This specifies whether password is a required field when creating a new user. True by default; ignored if ``WAGTAILUSERS_PASSWORD_ENABLED`` is false. If this is set to False, and the password field is left blank when creating a user, then that user will have no usable password; in order to log in, they will have to reset their password (if ``WAGTAIL_PASSWORD_RESET_ENABLED`` is True) or use an alternative authentication system such as LDAP (if one is set up).

.. code-block:: python

  WAGTAIL_EMAIL_MANAGEMENT_ENABLED = True

This specifies whether users are allowed to change their email (enabled by default).

.. _email_notifications:

Email Notifications
-------------------

.. code-block:: python

  WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'wagtail@myhost.io'

Wagtail sends email notifications when content is submitted for moderation, and when the content is accepted or rejected. This setting lets you pick which email address these automatic notifications will come from. If omitted, Django will fall back to using the ``DEFAULT_FROM_EMAIL`` variable if set, and ``webmaster@localhost`` if not.

.. code-block:: python

  WAGTAILADMIN_NOTIFICATION_USE_HTML = True

Notification emails are sent in `text/plain` by default, change this to use HTML formatting.

.. code-block:: python

  WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS = False

Notification emails are sent to moderators and superusers by default. You can change this to exclude superusers and only notify moderators.

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

As above, but for password restrictions on documents. For more details, see the :ref:`private_pages` documentation.


Login page
----------

The basic login page can be customised with a custom template.

.. code-block:: python

  WAGTAIL_FRONTEND_LOGIN_TEMPLATE = 'myapp/login.html'

Or the login page can be a redirect to an external or internal URL.

.. code-block:: python

  WAGTAIL_FRONTEND_LOGIN_URL = '/accounts/login/'

For more details, see the :ref:`login_page` documentation.



Case-Insensitive Tags
---------------------

.. code-block:: python

  TAGGIT_CASE_INSENSITIVE = True

Tags are case-sensitive by default ('music' and 'Music' are treated as distinct tags). In many cases the reverse behaviour is preferable.

Multi-word tags
---------------

.. code-block:: python

  TAG_SPACES_ALLOWED = False

Tags can only consist of a single word, no spaces allowed. The default setting is ``True`` (spaces in tags are allowed).

Tag limit
---------

.. code-block:: python

  TAG_LIMIT = 5

Limit the number of tags that can be added to (django-taggit) Tag model. Default setting is ``None``, meaning no limit on tags.

Unicode Page Slugs
------------------

.. code-block:: python

  WAGTAIL_ALLOW_UNICODE_SLUGS = True

By default, page slugs can contain any alphanumeric characters, including non-Latin alphabets. Set this to False to limit slugs to ASCII characters.

.. _WAGTAIL_AUTO_UPDATE_PREVIEW:

Auto update preview
-------------------

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

.. _WAGTAIL_USAGE_COUNT_ENABLED:

Usage for images, documents and snippets
----------------------------------------

.. code-block:: python

    WAGTAIL_USAGE_COUNT_ENABLED = True

When enabled Wagtail shows where a particular image, document or snippet is being used on your site.
This is disabled by default because it generates a query which may run slowly on sites with large numbers of pages.

A link will appear on the edit page (in the rightmost column) showing you how many times the item is used.
Clicking this link takes you to the "Usage" page, which shows you where the snippet, document or image is used.

The link is also shown on the delete page, above the "Delete" button.

.. note::

    The usage count only applies to direct (database) references. Using documents, images and snippets within StreamFields or rich text fields will not be taken into account.

Date and DateTime inputs
------------------------

.. code-block:: python

    WAGTAIL_DATE_FORMAT = '%d.%m.%Y.'
    WAGTAIL_DATETIME_FORMAT = '%d.%m.%Y. %H:%M'


Specifies the date and datetime format to be used in input fields in the Wagtail admin. The format is specified in `Python datetime module syntax <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_, and must be one of the recognised formats listed in the ``DATE_INPUT_FORMATS`` or ``DATETIME_INPUT_FORMATS`` setting respectively (see `DATE_INPUT_FORMATS <https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-DATE_INPUT_FORMATS>`_).

.. _WAGTAIL_USER_TIME_ZONES:

Time zones
----------

Logged-in users can choose their current time zone for the admin interface in the account settings.  If is no time zone selected by the user, then ``TIME_ZONE`` will be used.
(Note that time zones are only applied to datetime fields, not to plain time or date fields.  This is a Django design decision.)

The list of time zones is by default the common_timezones list from pytz.
It is possible to override this list via the ``WAGTAIL_USER_TIME_ZONES`` setting.
If there is zero or one time zone permitted, the account settings form will be hidden.

.. code-block:: python

    WAGTAIL_USER_TIME_ZONES = ['America/Chicago', 'Australia/Sydney', 'Europe/Rome']

.. _WAGTAILADMIN_PERMITTED_LANGUAGES:

Admin languages
---------------

Users can choose between several languages for the admin interface
in the account settings. The list of languages is by default all the available
languages in Wagtail with at least 90% coverage. To change it, set ``WAGTAILADMIN_PERMITTED_LANGUAGES``:

.. code-block:: python

    WAGTAILADMIN_PERMITTED_LANGUAGES = [('en', 'English'),
                                        ('pt', 'Portuguese')]

Since the syntax is the same as Django ``LANGUAGES``, you can do this so users
can only choose between front office languages:

.. code-block:: python

    LANGUAGES = WAGTAILADMIN_PERMITTED_LANGUAGES = [('en', 'English'),
                                                    ('pt', 'Portuguese')]


API Settings
------------

For full documenation on API configuration, including these settings, see :ref:`api_v2_configuration` documentation.

.. code-block:: python

    WAGTAILAPI_BASE_URL = 'http://api.example.com/'

Required when using frontend cache invalidation, used to generate absolute URLs to document files and invalidating the cache.


.. code-block:: python

    WAGTAILAPI_LIMIT_MAX = 500

Default is 20, used to change the maximum number of results a user can request at a time, set to ``None`` for no limit.


.. code-block:: python

    WAGTAILAPI_SEARCH_ENABLED = False

Default is true, setting this to false will disable full text search on all endpoints.

.. code-block:: python

    WAGTAILAPI_USE_FRONTENDCACHE = True

Requires ``wagtailfrontendcache`` app to be installed, inidicates the API should use the frontend cache.


Frontend cache
--------------

For full documenation on frontend cache invalidation, including these settings, see :ref:`frontend_cache_purging`.


.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'varnish': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
            'LOCATION': 'http://localhost:8000',
        },
    }

See documentation linked above for full options available.

.. note::

    ``WAGTAILFRONTENDCACHE_LOCATION`` is no longer the preferred way to set the cache location, instead set the ``LOCATION`` within the ``WAGTAILFRONTENDCACHE`` item.


.. code-block:: python

    WAGTAILFRONTENDCACHE_LANGUAGES = [l[0] for l in settings.LANGUAGES]

Default is an empty list, must be a list of languages to also purge the urls for each language of a purging url. This setting needs ``settings.USE_I18N`` to be ``True`` to work.



.. _WAGTAILADMIN_RICH_TEXT_EDITORS:

Rich text
---------

.. code-block:: python

    WAGTAILADMIN_RICH_TEXT_EDITORS = {
        'default': {
            'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
            'OPTIONS': {
                'features': ['h2', 'bold', 'italic', 'link', 'document-link']
            }
        },
        'legacy': {
            'WIDGET': 'wagtail.admin.rich_text.HalloRichTextArea',
        }
    }

Customise the behaviour of rich text fields. By default, ``RichTextField`` and ``RichTextBlock`` use the configuration given under the ``'default'`` key, but this can be overridden on a per-field basis through the ``editor`` keyword argument, e.g. ``body = RichTextField(editor='legacy')``. Within each configuration block, the following fields are recognised:

 * ``WIDGET``: The rich text widget implementation to use. Wagtail provides two implementations: ``wagtail.admin.rich_text.DraftailRichTextArea`` (a modern extensible editor which enforces well-structured markup) and ``wagtail.admin.rich_text.HalloRichTextArea`` (deprecated; works directly at the HTML level). Other widgets may be provided by third-party packages.

 * ``OPTIONS``: Configuration options to pass to the widget. Recognised options are widget-specific, but both ``DraftailRichTextArea`` and ``HalloRichTextArea`` accept a ``features`` list indicating the active rich text features (see :ref:`rich_text_features`).



URL Patterns
~~~~~~~~~~~~

.. code-block:: python

  from django.contrib import admin

  from wagtail.core import urls as wagtail_urls
  from wagtail.admin import urls as wagtailadmin_urls
  from wagtail.documents import urls as wagtaildocs_urls

  urlpatterns = [
      re_path(r'^django-admin/', include(admin.site.urls)),

      re_path(r'^admin/', include(wagtailadmin_urls)),
      re_path(r'^documents/', include(wagtaildocs_urls)),

      # Optional URL for including your own vanilla Django urls/views
      re_path(r'', include('myapp.urls')),

      # For anything not caught by a more specific rule above, hand over to
      # Wagtail's serving mechanism
      re_path(r'', include(wagtail_urls)),
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
      'wagtail.core',

      'taggit',
      'modelcluster',

      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',
  ]


  MIDDLEWARE = [
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.middleware.common.CommonMiddleware',
      'django.middleware.csrf.CsrfViewMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'django.middleware.clickjacking.XFrameOptionsMiddleware',
      'django.middleware.security.SecurityMiddleware',

      'wagtail.core.middleware.SiteMiddleware',
      'wagtail.contrib.redirects.middleware.RedirectMiddleware',
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

  WSGI_APPLICATION = 'myproject.wsgi.application'

  # Database

  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql',
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
  #    'BACKEND': 'wagtail.search.backends.elasticsearch2',
  #    'INDEX': 'myapp'
  #  }
  #}

  # Wagtail email notifications from address
  # WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = 'wagtail@myhost.io'

  # Wagtail email notification format
  # WAGTAILADMIN_NOTIFICATION_USE_HTML = True

  # Reverse the default case-sensitive handling of tags
  TAGGIT_CASE_INSENSITIVE = True


``urls.py``
-----------

.. code-block:: python

  from django.conf.urls import include, re_path
  from django.conf.urls.static import static
  from django.views.generic.base import RedirectView
  from django.contrib import admin
  from django.conf import settings
  import os.path

  from wagtail.core import urls as wagtail_urls
  from wagtail.admin import urls as wagtailadmin_urls
  from wagtail.documents import urls as wagtaildocs_urls


  urlpatterns = [
      re_path(r'^django-admin/', include(admin.site.urls)),

      re_path(r'^admin/', include(wagtailadmin_urls)),
      re_path(r'^documents/', include(wagtaildocs_urls)),

      # For anything not caught by a more specific rule above, hand over to
      # Wagtail's serving mechanism
      re_path(r'', include(wagtail_urls)),
  ]


  if settings.DEBUG:
      from django.contrib.staticfiles.urls import staticfiles_urlpatterns

      urlpatterns += staticfiles_urlpatterns() # tell gunicorn where static files are in dev mode
      urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
      urlpatterns += [
          re_path(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'myapp/images/favicon.ico'))
      ]
