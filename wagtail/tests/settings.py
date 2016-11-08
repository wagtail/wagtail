from __future__ import absolute_import, unicode_literals

import os

import django

WAGTAIL_ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, 'tests', 'test-static')
MEDIA_ROOT = os.path.join(WAGTAIL_ROOT, 'tests', 'test-media')
MEDIA_URL = '/media/'

TIME_ZONE = 'Asia/Tokyo'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', 'wagtail'),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASS', None),
        'HOST': os.environ.get('DATABASE_HOST', None),

        'TEST': {
            'NAME': os.environ.get('DATABASE_NAME', None),
        }
    }
}


SECRET_KEY = 'not needed'

ROOT_URLCONF = 'wagtail.tests.urls'

STATIC_URL = '/static/'
STATIC_ROOT = STATIC_ROOT

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'wagtail.tests.context_processors.do_not_use_static_url',
                'wagtail.contrib.settings.context_processors.settings',
            ],
            'debug': True,
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': False,
        'DIRS': [
            os.path.join(WAGTAIL_ROOT, 'tests', 'testapp', 'jinja2_templates'),
        ],
        'OPTIONS': {
            'extensions': [
                'wagtail.wagtailcore.jinja2tags.core',
                'wagtail.wagtailadmin.jinja2tags.userbar',
                'wagtail.wagtailimages.jinja2tags.images',
                'wagtail.contrib.settings.jinja2tags.settings',
            ],
        },
    },
]

if django.VERSION >= (1, 10):
    MIDDLEWARE = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        'wagtail.wagtailcore.middleware.SiteMiddleware',
        'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',

        'wagtail.wagtailcore.middleware.SiteMiddleware',
        'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    )

INSTALLED_APPS = (
    # Install wagtailredirects with its appconfig
    # Theres nothing special about wagtailredirects, we just need to have one
    # app which uses AppConfigs to test that hooks load properly
    'wagtail.wagtailredirects.apps.WagtailRedirectsAppConfig',

    'wagtail.tests.testapp',
    'wagtail.tests.demosite',
    'wagtail.tests.customuser',
    'wagtail.tests.snippets',
    'wagtail.tests.routablepage',
    'wagtail.tests.search',
    'wagtail.tests.modeladmintest',
    'wagtail.contrib.wagtailstyleguide',
    'wagtail.contrib.wagtailsitemaps',
    'wagtail.contrib.wagtailroutablepage',
    'wagtail.contrib.wagtailfrontendcache',
    'wagtail.contrib.wagtailapi',
    'wagtail.contrib.wagtailsearchpromotions',
    'wagtail.contrib.settings',
    'wagtail.contrib.modeladmin',
    'wagtail.contrib.table_block',
    'wagtail.wagtailforms',
    'wagtail.wagtailsearch',
    'wagtail.wagtailembeds',
    'wagtail.wagtailimages',
    'wagtail.wagtailsites',
    'wagtail.wagtailusers',
    'wagtail.wagtailsnippets',
    'wagtail.wagtaildocs',
    'wagtail.wagtailadmin',
    'wagtail.api.v2',
    'wagtail.wagtailcore',

    'taggit',
    'rest_framework',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)


# Using DatabaseCache to make sure that the cache is cleared between tests.
# This prevents false-positives in some wagtail core tests where we are
# changing the 'wagtail_root_paths' key which may cause future tests to fail.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
)


WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.backends.db',
    }
}

AUTH_USER_MODEL = 'customuser.CustomUser'

if 'ELASTICSEARCH_URL' in os.environ:
    if os.environ.get('ELASTICSEARCH_VERSION') == '5':
        backend = 'wagtail.wagtailsearch.backends.elasticsearch5'
    elif os.environ.get('ELASTICSEARCH_VERSION') == '2':
        backend = 'wagtail.wagtailsearch.backends.elasticsearch2'
    else:
        backend = 'wagtail.wagtailsearch.backends.elasticsearch'

    WAGTAILSEARCH_BACKENDS['elasticsearch'] = {
        'BACKEND': backend,
        'URLS': [os.environ['ELASTICSEARCH_URL']],
        'TIMEOUT': 10,
        'max_retries': 1,
        'AUTO_UPDATE': False,
    }


WAGTAIL_SITE_NAME = "Test Site"

# Extra user field for custom user edit and create form tests. This setting
# needs to here because it is used at the module level of wagtailusers.forms
# when the module gets loaded. The decorator 'override_settings' does not work
# in this scenario.
WAGTAIL_USER_CUSTOM_FIELDS = ['country', 'attachment']

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.wagtailadmin.rich_text.HalloRichTextArea'
    },
    'custom': {
        'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
    },
}
