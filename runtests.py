#!/usr/bin/env python

import argparse
import os
import shutil
import sys
import warnings

from django.core.management import execute_from_command_line
from django.test.selenium import SeleniumTestCaseBase


os.environ['DJANGO_SETTINGS_MODULE'] = 'wagtail.tests.settings'


class ActionSelenium(argparse.Action):
    """
    Validate the comma-separated list of requested browsers.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        browsers = values.split(',')
        for browser in browsers:
            try:
                SeleniumTestCaseBase.import_webdriver(browser)
            except ImportError:
                raise argparse.ArgumentError(self, "Selenium browser specification '%s' is not valid." % browser)
        setattr(namespace, self.dest, browsers)


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deprecation', choices=['all', 'pending', 'imminent', 'none'], default='imminent')
    parser.add_argument('--postgres', action='store_true')
    parser.add_argument('--elasticsearch5', action='store_true')
    parser.add_argument('--elasticsearch6', action='store_true')
    parser.add_argument('--elasticsearch7', action='store_true')
    parser.add_argument('--emailuser', action='store_true')
    parser.add_argument('--disabletimezone', action='store_true')
    parser.add_argument('--bench', action='store_true')
    parser.add_argument(
        '--selenium', action=ActionSelenium, metavar='BROWSERS',
        help='A comma-separated list of browsers to run the Selenium tests against.',
    )
    parser.add_argument('--selenium-headless', action='store_true')
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

    if args.elasticsearch5:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        os.environ.setdefault('ELASTICSEARCH_VERSION', '5')
    elif args.elasticsearch6:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        os.environ.setdefault('ELASTICSEARCH_VERSION', '6')
    elif args.elasticsearch7:
        os.environ.setdefault('ELASTICSEARCH_URL', 'http://localhost:9200')
        os.environ.setdefault('ELASTICSEARCH_VERSION', '7')

    elif 'ELASTICSEARCH_URL' in os.environ:
        # forcibly delete the ELASTICSEARCH_URL setting to skip those tests
        del os.environ['ELASTICSEARCH_URL']

    if args.emailuser:
        os.environ['USE_EMAIL_USER_MODEL'] = '1'

    if args.disabletimezone:
        os.environ['DISABLE_TIMEZONE'] = '1'

    if args.selenium:
        execute_from_command_line([sys.argv[0], 'collectstatic'])

        SeleniumTestCaseBase.browsers = args.selenium
        SeleniumTestCaseBase.headless = args.selenium_headless

        argv = [sys.argv[0], 'test', '--tag=selenium'] + rest

    elif args.bench:
        benchmarks = [
            'wagtail.admin.tests.benches',
        ]

        argv = [sys.argv[0], 'test', '-v2'] + benchmarks + rest
    else:
        argv = [sys.argv[0], 'test'] + rest

    try:
        execute_from_command_line(argv)
    finally:
        from wagtail.tests.settings import MEDIA_ROOT, STATIC_ROOT
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
