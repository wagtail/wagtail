import os

from django.conf import global_settings


WAGTAIL_ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, 'test-static')
MEDIA_ROOT = os.path.join(WAGTAIL_ROOT, 'test-media')
MEDIA_URL = '/media/'


DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql_psycopg2'),
        'NAME': os.environ.get('DATABASE_NAME', 'wagtaildemo'),
        'TEST_NAME': os.environ.get('DATABASE_NAME', 'test_wagtaildemo'),
        'USER': os.environ.get('DATABASE_USER', 'postgres'),
        'PASSWORD': os.environ.get('DATABASE_PASS', None),
        'HOST': os.environ.get('DATABASE_HOST', None),
        'PORT': os.environ.get('DATABASE_PORT', None),
    }
}


SECRET_KEY = 'not needed'

ROOT_URLCONF='wagtail.tests.urls'

STATIC_URL = '/static/'
STATIC_ROOT = STATIC_ROOT

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

USE_TZ = True

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',

    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
)

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'taggit',
    'compressor',

    'wagtail.wagtailcore',
    'wagtail.wagtailadmin',
    'wagtail.wagtaildocs',
    'wagtail.wagtailsnippets',
    'wagtail.wagtailusers',
    'wagtail.wagtailsites',
    'wagtail.wagtailimages',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsearch',
    'wagtail.wagtailforms',
    'wagtail.contrib.wagtailstyleguide',
    'wagtail.contrib.wagtailsitemaps',
    'wagtail.contrib.wagtailroutablepage',
    'wagtail.contrib.wagtailfrontendcache',
    'wagtail.tests',
]


# Install wagtailredirects with its appconfig
# Theres nothing special about wagtailredirects, we just need to have one
# app which uses AppConfigs to test that hooks load properly

INSTALLED_APPS.append('wagtail.wagtailredirects.apps.WagtailRedirectsAppConfig')


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

COMPRESS_ENABLED = False  # disable compression so that we can run tests on the content of the compress tag


WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.backends.db.DBSearch',
    }
}

AUTH_USER_MODEL = 'tests.CustomUser'

try:
    # Only add Elasticsearch backend if the elasticsearch-py library is installed
    import elasticsearch

    # Import succeeded, add an Elasticsearch backend
    WAGTAILSEARCH_BACKENDS['elasticsearch'] = {
        'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
        'TIMEOUT': 10,
        'max_retries': 1,
    }

    # Check if we're running in Drone
    if 'ELASTICSEARCH_URL' in os.environ:
        WAGTAILSEARCH_BACKENDS['elasticsearch']['URLS'] = [os.environ['ELASTICSEARCH_URL']]

except ImportError:
    pass


WAGTAIL_SITE_NAME = "Test Site"
