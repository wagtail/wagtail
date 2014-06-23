from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.six.moves.urllib.parse import urlparse, ParseResult
from django.http import QueryDict

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
