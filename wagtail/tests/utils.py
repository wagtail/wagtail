from django.contrib.auth.models import User

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
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')
