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
        import elasticutils
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
            'wagtail.tests',
        ],
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
        ),
        COMPRESS_ENABLED=False,  # disable compression so that we can run tests on the content of the compress tag
        WAGTAILSEARCH_BACKENDS=WAGTAILSEARCH_BACKENDS,
        WAGTAIL_SITE_NAME='Test Site'
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
