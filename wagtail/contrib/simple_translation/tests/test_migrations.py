from django.contrib.auth.models import Permission
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
