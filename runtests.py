#!/usr/bin/env python

import argparse
import os
import shutil
import sys
import warnings

from django.core.management import execute_from_command_line

os.environ["DJANGO_SETTINGS_MODULE"] = "wagtail.test.settings"


def make_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deprecation",
        choices=["all", "pending", "imminent", "none"],
        default="imminent",
    )
    parser.add_argument("--postgres", action="store_true")
    parser.add_argument("--elasticsearch5", action="store_true")
    parser.add_argument("--elasticsearch6", action="store_true")
    parser.add_argument("--elasticsearch7", action="store_true")
    parser.add_argument("--emailuser", action="store_true")
    parser.add_argument("--disabletimezone", action="store_true")
    parser.add_argument("--bench", action="store_true")
    return parser


def parse_args(args=None):
    return make_parser().parse_known_args(args)


def runtests():
    args, rest = parse_args()

    only_wagtail = r"^wagtail(\.|$)"
    if args.deprecation == "all":
        # Show all deprecation warnings from all packages
        warnings.simplefilter("default", DeprecationWarning)
        warnings.simplefilter("default", PendingDeprecationWarning)
    elif args.deprecation == "pending":
        # Show all deprecation warnings from wagtail
        warnings.filterwarnings(
            "default", category=DeprecationWarning, module=only_wagtail
        )
        warnings.filterwarnings(
            "default", category=PendingDeprecationWarning, module=only_wagtail
        )
    elif args.deprecation == "imminent":
        # Show only imminent deprecation warnings from wagtail
        warnings.filterwarnings(
            "default", category=DeprecationWarning, module=only_wagtail
        )
    elif args.deprecation == "none":
        # Deprecation warnings are ignored by default
        pass

    if args.postgres:
        os.environ["DATABASE_ENGINE"] = "django.db.backends.postgresql"

    if args.elasticsearch5:
        os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")
        os.environ.setdefault("ELASTICSEARCH_VERSION", "5")
    elif args.elasticsearch6:
        os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")
        os.environ.setdefault("ELASTICSEARCH_VERSION", "6")
    elif args.elasticsearch7:
        os.environ.setdefault("ELASTICSEARCH_URL", "http://localhost:9200")
        os.environ.setdefault("ELASTICSEARCH_VERSION", "7")

    elif "ELASTICSEARCH_URL" in os.environ:
        # forcibly delete the ELASTICSEARCH_URL setting to skip those tests
        del os.environ["ELASTICSEARCH_URL"]

    if args.emailuser:
        os.environ["USE_EMAIL_USER_MODEL"] = "1"

    if args.disabletimezone:
        os.environ["DISABLE_TIMEZONE"] = "1"

    if args.bench:
        benchmarks = [
            "wagtail.admin.tests.benches",
        ]

        argv = [sys.argv[0], "test", "-v2"] + benchmarks + rest
    else:
        argv = [sys.argv[0], "test"] + rest

    try:
        execute_from_command_line(argv)
    finally:
        from wagtail.test.settings import MEDIA_ROOT, STATIC_ROOT

        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == "__main__":
    runtests()
