#!/usr/bin/env python
import sys
import os
import shutil

from django.conf import settings
from django.core.management import execute_from_command_line

from wagtail.tests.settings import SETTINGS, STATIC_ROOT, MEDIA_ROOT


if not settings.configured:
    settings.configure(**SETTINGS)


def runtests():
    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    try:
        execute_from_command_line(argv)
    finally:
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
