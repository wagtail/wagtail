#!/usr/bin/env python
""" toxhelper is a simple wrapper of pytest and coverage to be used with tox.

It is specially useful to avoid path and interpreter problems while running
tests with jenkins in OS X, Linux and Windows using the same configuration.

See https://tabo.pe/jenkins/ for the results.
"""

import sys

import os
import pytest

from coverage import coverage


def run_the_tests():
    if 'TOX_DB' in os.environ:
        os.environ['DATABASE_HOST'], os.environ['DATABASE_PORT'] = {
            'pgsql': ('dummy_test_database_server', '5434'),
            'mysql': ('dummy_test_database_server', '3308'),
            'sqlite': ('', ''),
        }[os.environ['TOX_DB']]
    cov = coverage()
    cov.start()
    test_result = pytest.main(sys.argv[1:])
    cov.stop()
    cov.save()
    return test_result

if __name__ == '__main__':
    sys.exit(run_the_tests())
