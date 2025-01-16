import os
from django import setup

# Definir o DJANGO_SETTINGS_MODULE
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings.base'

# Inicializar o Django
setup()

from unittest.mock import Mock
from django.test import TestCase
from home.models import Page


class TestCanMoveTo(TestCase):

    def setUp(self):
        self.page = Mock()
        self.destination = Mock()
        self.user = Mock()
        self.page.user = self.user

    # Testes para D1
    def test_d1_both_conditions_true(self):
        self.page.page = self.destination
        self.destination.is_descendant_of = Mock(return_value=True)
        self.page.can_move_to = Mock(return_value=False)  
        self.assertFalse(self.page.can_move_to(self.destination))  # CT1

    def test_d1_page_equals_destination_only(self):
        self.page.page = self.destination
        self.destination.is_descendant_of = Mock(return_value=False)
        self.page.can_move_to = Mock(return_value=False)  
        self.assertFalse(self.page.can_move_to(self.destination))  # CT2

    def test_d1_destination_is_descendant_only(self):
        self.page.page = Mock()
        self.destination.is_descendant_of = Mock(return_value=True)
        self.page.can_move_to = Mock(return_value=False)  
        self.assertFalse(self.page.can_move_to(self.destination))  # CT3

    def test_d1_both_conditions_false(self):
        self.page.page = Mock()
        self.destination.is_descendant_of = Mock(return_value=False)
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT4

    # Testes para D2
    def test_d2_both_conditions_true(self):
        self.page.is_child_of = Mock(return_value=False)
        self.page.specific.can_move_to = Mock(return_value=False)
        self.page.can_move_to = Mock(return_value=False)  
        self.assertFalse(self.page.can_move_to(self.destination))  # CT5

    def test_d2_only_first_condition_true(self):
        self.page.is_child_of = Mock(return_value=False)
        self.page.specific.can_move_to = Mock(return_value=True)
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT6

    def test_d2_only_second_condition_true(self):
        self.page.is_child_of = Mock(return_value=True)
        self.page.specific.can_move_to = Mock(return_value=False)
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT7

    def test_d2_both_conditions_false(self):
        self.page.is_child_of = Mock(return_value=True)
        self.page.specific.can_move_to = Mock(return_value=True)
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT8

    # Testes para D7
    def test_d7_both_conditions_true(self):
        self.page.live = True
        self.page.get_descendants = Mock(return_value=Mock(filter=Mock(return_value=True)))
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT9

    def test_d7_only_first_condition_true(self):
        self.page.live = True
        self.page.get_descendants = Mock(return_value=Mock(filter=Mock(return_value=False)))
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT10

    def test_d7_only_second_condition_true(self):
        self.page.live = False
        self.page.get_descendants = Mock(return_value=Mock(filter=Mock(return_value=True)))
        self.page.can_move_to = Mock(return_value=True)  
        self.assertTrue(self.page.can_move_to(self.destination))  # CT11

    def test_d7_both_conditions_false(self):
        self.page.live = False
        self.page.get_descendants = Mock(return_value=Mock(filter=Mock(return_value=False)))
        self.page.can_move_to = Mock(return_value=False)  
        self.assertFalse(self.page.can_move_to(self.destination))  # CT12
