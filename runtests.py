#!/usr/bin/env python

from __future__ import absolute_import, unicode_literals

import argparse
import os
import shutil
import sys
import warnings

from django.core.management import execute_from_command_line

os.environ['DJANGO_SETTINGS_MODULE'] = 'wagtail.tests.settings'


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deprecation', choices=['all', 'pending', 'imminent', 'none'], default='imminent')
    parser.add_argument('--postgres', action='store_true')
    parser.add_argument('--elasticsearch2', action='store_true')
    parser.add_argument('--elasticsearch5', action='store_true')
    return parser


def parse_args(args=None):
    return make_parser().parse_known_args(args)


def runtests():
    args, rest = parse_args()

    only_wagtail = r'^wagtail(\.|$)'
    if args.deprecation == 'all':
        # Show all deprecation warnings from all packages
        warnings.simplefilter('default', DeprecationWarning)
        warnings.simplefilter('default', PendingDeprecationWarning)
    elif args.deprecation == 'pending':
        # Show all deprecation warnings from wagtail
        warnings.filterwarnings('default', category=DeprecationWarning, module=only_wagtail)
        warnings.filterwarnings('default', category=PendingDeprecationWarning, module=only_wagtail)
    elif args.deprecation == 'imminent':
        # Show only imminent deprecation warnings from wagtail
        warnings.filterwarnings('default', category=DeprecationWarning, module=only_wagtail)
    elif args.deprecation == 'none':
        # Deprecation warnings are ignored by default
        pass

    if args.postgres:
        os.environ['DATABASE_ENGINE'] = 'django.db.backends.postgresql'

    if args.elasticsearch2:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        os.environ.setdefault('ELASTICSEARCH_VERSION', '2')
    elif args.elasticsearch5:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        os.environ.setdefault('ELASTICSEARCH_VERSION', '5')

        if args.elasticsearch2:
            raise RuntimeError("You cannot test both Elasticsearch 2 and 5 together")
    elif 'ELASTICSEARCH_URL' in os.environ:
        # forcibly delete the ELASTICSEARCH_URL setting to skip those tests
        del os.environ['ELASTICSEARCH_URL']

    argv = [sys.argv[0], 'test'] + rest
    try:
        execute_from_command_line(argv)
    finally:
        from wagtail.tests.settings import STATIC_ROOT, MEDIA_ROOT
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
