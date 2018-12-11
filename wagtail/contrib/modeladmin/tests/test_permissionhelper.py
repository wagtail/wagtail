from django.test import TestCase

from wagtail.tests.modeladmintest.models import Author, LegendaryAuthor
from wagtail.contrib.modeladmin.helpers import PermissionHelper


class TestPermissionHelper(TestCase):

    def test_get_all_model_permissions_returns_permissions_for_concrete_model(self):
        # This test will pass
        instance = PermissionHelper(model=Author)
        result = instance.get_all_model_permissions()
        result_codenames = result.values_list('codename', flat=True)
        for codename in ('add_author', 'change_author', 'delete_author'):
            self.assertIn(codename, result_codenames)

    def test_get_all_model_permissions_returns_permissions_for_proxy_model(self):
        # This test will fail
        instance = PermissionHelper(model=LegendaryAuthor)
        result = instance.get_all_model_permissions()
        result_codenames = result.values_list('codename', flat=True)
        for codename in ('add_legendaryauthor', 'change_legendaryauthor', 'delete_legendaryauthor'):
            self.assertIn(codename, result_codenames)
