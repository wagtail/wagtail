#!/usr/bin/env python
import sys
import os
import shutil
import warnings

from django.core.management import execute_from_command_line

from wagtail.tests.settings import STATIC_ROOT, MEDIA_ROOT


os.environ['DJANGO_SETTINGS_MODULE'] = 'wagtail.tests.settings'


def runtests():
    # Don't ignore DeprecationWarnings
    warnings.simplefilter('default', DeprecationWarning)
    warnings.simplefilter('default', PendingDeprecationWarning)

    argv = sys.argv[:1] + ['test'] + sys.argv[1:]
    try:
        execute_from_command_line(argv)
    finally:
        shutil.rmtree(STATIC_ROOT, ignore_errors=True)
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


if __name__ == '__main__':
    runtests()
