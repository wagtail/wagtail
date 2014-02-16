#!/usr/bin/env python
import sys, os, shutil

from django.conf import settings, global_settings
from django.core.management import execute_from_command_line

WAGTAIL_ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, 'test-static')

if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': 'wagtaildemo',
            }
        },
        ROOT_URLCONF='wagtail.tests.urls',
        STATIC_URL='/static/',
        STATIC_ROOT=STATIC_ROOT,
        STATICFILES_FINDERS = (
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
        ]
    )


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    try:
        execute_from_command_line(argv)
    finally:
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()

