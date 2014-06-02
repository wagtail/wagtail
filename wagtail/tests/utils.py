from django.test import TestCase
from django.contrib.auth.models import User
from django.utils.six.moves.urllib.parse import urlparse, ParseResult

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


def login(client):
    # Create a user
    user = User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')

    return user


class WagtailTestUtils(object):
    def login(self):
        return login(self.client)

    # From: https://github.com/django/django/blob/255449c1ee61c14778658caae8c430fa4d76afd6/django/contrib/auth/tests/test_views.py#L70-L85
    def assertURLEqual(self, url, expected, parse_qs=False):
        """
        Given two URLs, make sure all their components (the ones given by
        urlparse) are equal, only comparing components that are present in both
        URLs.
        If `parse_qs` is True, then the querystrings are parsed with QueryDict.
        This is useful if you don't want the order of parameters to matter.
        Otherwise, the query strings are compared as-is.
        """
        fields = ParseResult._fields

        for attr, x, y in zip(fields, urlparse(url), urlparse(expected)):
            if parse_qs and attr == 'query':
                x, y = QueryDict(x), QueryDict(y)
            if x and y and x != y:
                self.fail("%r != %r (%s doesn't match)" % (url, expected, attr))
