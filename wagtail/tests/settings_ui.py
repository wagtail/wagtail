from .settings import *  # noqa


# Settings meant to run the test suite with Django’s development server, for integration tests.
DEBUG = True

DATABASES['default']['NAME'] = 'ui_tests.db'  # noqa

WAGTAIL_EXPERIMENTAL_FEATURES = {'slim-sidebar'}
