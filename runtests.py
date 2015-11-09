#!/usr/bin/env python

import sys
import os
import shutil
import warnings

from django.core.management import execute_from_command_line


os.environ['DJANGO_SETTINGS_MODULE'] = 'wagtail.tests.settings'


def runtests():
    # Don't ignore DeprecationWarnings
    warnings.simplefilter('default', DeprecationWarning)
    warnings.simplefilter('default', PendingDeprecationWarning)

    args = sys.argv[1:]

    if '--postgres' in args:
        os.environ['DATABASE_ENGINE'] = 'django.db.backends.postgresql_psycopg2'
        args.remove('--postgres')

    if '--elasticsearch' in args:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        args.remove('--elasticsearch')

    argv = sys.argv[:1] + ['test'] + args
    try:
        execute_from_command_line(argv)
    finally:
        from wagtail.tests.settings import STATIC_ROOT, MEDIA_ROOT
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
