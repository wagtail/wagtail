from django.contrib.auth.models import User

try:
    import unittest

    # Check if this is unittest2
    assert hasattr(unittest, 'skip')
except (ImportError, AssertionError):
    import unittest2 as unittest


def login(client):
    # Create a user
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')