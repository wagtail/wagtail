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

    def test_ct1_usuario_a_ser_deletado_e_superusuario_e_usuario_atual_nao(self):
        self.user_to_delete.is_superuser = True
        self.current_user.is_superuser = False
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertFalse(result)

    def test_ct2_usuario_a_ser_deletado_e_superusuario_e_usuario_atual_tambem(self):
        self.user_to_delete.is_superuser = True
        self.current_user.is_superuser = True
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertTrue(result)

    def test_ct3_usuario_a_ser_deletado_nao_e_superusuario_e_usuario_atual_e(self):
        self.user_to_delete.is_superuser = False
        self.current_user.is_superuser = True
        
        result = user_can_delete_user(self.current_user, self.user_to_delete)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
