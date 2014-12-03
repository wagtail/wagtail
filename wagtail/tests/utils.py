from contextlib import contextmanager
import warnings
import threading

from django.contrib.auth import get_user_model
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
        user = get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')

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


# from http://www.caktusgroup.com/blog/2009/05/26/testing-django-views-for-concurrency-issues/
def test_concurrently(times):
    """
    Add this decorator to small pieces of code that you want to test
    concurrently to make sure they don't raise exceptions when run at the
    same time.  E.g., some Django views that do a SELECT and then a subsequent
    INSERT might fail when the INSERT assumes that the data has not changed
    since the SELECT.
    """
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []
            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception as e:
                    exceptions.append(e)
                    raise
            threads = []
            for i in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception('test_concurrently intercepted %s exceptions: %s' % (len(exceptions), exceptions))
        return wrapper
    return test_concurrently_decorator
