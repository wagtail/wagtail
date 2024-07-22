import unittest
from unittest.mock import Mock
import os

from django.test import TestCase
from django.conf import settings
from wagtail.users.utils import user_can_delete_user

os.environ['DJANGO_SETTINGS_MODULE'] = 'os.environ.setdefault'

class TestUserCanDeleteUser(TestCase):
    def setUp(self):
        
        self.current_user = Mock()
        
        self.user_to_delete = Mock()
        
        self.current_user.has_perm.return_value = True

    def user_to_be_deleted_is_superuser_and_current_user_is_not(self):
        self.user_to_delete.is_superuser = True
        self.current_user.is_superuser = False
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertFalse(result)

    def user_to_be_deleted_is_superuser_and_current_user_is_too(self):
        self.user_to_delete.is_superuser = True
        self.current_user.is_superuser = True
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertTrue(result)

    def user_to_be_deleted_is_not_superuser_and_current_user_is(self):
        self.user_to_delete.is_superuser = False
        self.current_user.is_superuser = True
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
