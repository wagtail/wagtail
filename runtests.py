#!/usr/bin/env python
import sys
import os
import shutil

from django.conf import settings, global_settings
from django.core.management import execute_from_command_line

WAGTAIL_ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, 'test-static')
MEDIA_ROOT = os.path.join(WAGTAIL_ROOT, 'test-media')

if not settings.configured:

    try:
        import elasticsearch
        has_elasticsearch = True
    except ImportError:
        has_elasticsearch = False

    WAGTAILSEARCH_BACKENDS = {
        'default': {
            'BACKEND': 'wagtail.wagtailsearch.backends.db.DBSearch',
        }
    }
    if has_elasticsearch:
        WAGTAILSEARCH_BACKENDS['elasticsearch'] = {
            'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
            'TIMEOUT': 10,
            'max_retries': 1,
        }

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql_psycopg2'),
                'NAME': 'wagtaildemo',
                'USER': os.environ.get('DATABASE_USER', 'postgres'),
            }
        },
        ROOT_URLCONF='wagtail.tests.urls',
        STATIC_URL='/static/',
        STATIC_ROOT=STATIC_ROOT,
        MEDIA_ROOT=MEDIA_ROOT,
        USE_TZ=True,
        STATICFILES_FINDERS=(
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
            'compressor.finders.CompressorFinder',
        ),
        TEMPLATE_CONTEXT_PROCESSORS=global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
            'django.core.context_processors.request',
        ),
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',

            'wagtail.wagtailcore.middleware.SiteMiddleware',

            'wagtail.wagtailredirects.middleware.RedirectMiddleware',
        ),
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.auth',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'django.contrib.admin',

            'taggit',
            'south',
            'compressor',

            'wagtail.wagtailcore',
            'wagtail.wagtailadmin',
            'wagtail.wagtaildocs',
            'wagtail.wagtailsnippets',
            'wagtail.wagtailusers',
            'wagtail.wagtailimages',
            'wagtail.wagtailembeds',
            'wagtail.wagtailsearch',
            'wagtail.wagtailredirects',
            'wagtail.wagtailforms',
            'wagtail.contrib.wagtailstyleguide',
            'wagtail.contrib.wagtailsitemaps',
            'wagtail.tests',
        ],

        # Using DatabaseCache to make sure that the cache is cleared between tests.
        # This prevents false-positives in some wagtail core tests where we are
        # changing the 'wagtail_root_paths' key which may cause future tests to fail.
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'cache',
            }
        },
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
        ),
        COMPRESS_ENABLED=False,  # disable compression so that we can run tests on the content of the compress tag
        WAGTAILSEARCH_BACKENDS=WAGTAILSEARCH_BACKENDS,
        WAGTAIL_SITE_NAME='Test Site',
        LOGIN_REDIRECT_URL='wagtailadmin_home',
        LOGIN_URL='wagtailadmin_login',
    )


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    try:
        execute_from_command_line(argv)
    finally:
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
