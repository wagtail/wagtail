from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from wagtail.tests.utils import TestCase


class TestMigrations(TestCase):
    def test_content_type_exists(self):
        self.assertTrue(
            ContentType.objects.filter(
                app_label="simple_translation", model="simpletranslation"
            ).exists()
        )

    def test_permission_exists(self):
        self.assertTrue(
            Permission.objects.filter(codename="submit_translation").exists()
        )

    def test_groups_have_submit_translation_permission(self):
        perm = Permission.objects.get(codename="submit_translation")
        group = Group.objects.get(name="Editors")
        self.assertIn(perm, group.permissions.all())
        group = Group.objects.get(name="Moderators")
        self.assertIn(perm, group.permissions.all())
