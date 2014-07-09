from contextlib import contextmanager
import warnings

from django.contrib.auth.models import User
from django.utils import six

# We need to make sure that we're using the same unittest library that Django uses internally
# Otherwise, we get issues with the "SkipTest" and "ExpectedFailure" exceptions being recognised as errors
try:
    # Firstly, try to import unittest from Django
    from django.utils import unittest
except ImportError:
    # Django doesn't include unittest
    # We must be running on Django 1.7+ which doesn't support Python 2.6 so
    # the standard unittest library should be unittest2
    import unittest


class WagtailTestUtils(object):
    def login(self):
        # Create a user
        user = User.objects.create_superuser(username='test', email='test@email.com', password='password')

        # Login
        self.client.login(username='test', password='password')

        return user

    def assertRegex(self, *args, **kwargs):
        six.assertRegex(self, *args, **kwargs)

    @staticmethod
    @contextmanager
    def ignore_deprecation_warnings():
        with warnings.catch_warnings(record=True) as warning_list:  # catch all warnings
            yield

        # rethrow all warnings that were not DeprecationWarnings
        for w in warning_list:
            if not issubclass(w.category, DeprecationWarning):
                warnings.showwarning(message=w.message, category=w.category, filename=w.filename, lineno=w.lineno, file=w.file, line=w.line)
