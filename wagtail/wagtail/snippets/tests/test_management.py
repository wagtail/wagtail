from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import migrations
from django.test import TestCase

from wagtail.snippets.models import create_extra_permissions


class TestCreatePermissions(TestCase):
    def setUp(self):
        self.app_config = apps.get_app_config("auth")

    def tearDown(self):
        ContentType.objects.clear_cache()

    def test_unavailable_models(self):
        state = migrations.state.ProjectState()

        # Unavailable contenttypes.ContentType
        with self.assertNumQueries(0):
            create_extra_permissions(self.app_config, verbosity=0, apps=state.apps)

        # Unavailable auth.Permission
        state = migrations.state.ProjectState(real_apps={"contenttypes"})
        with self.assertNumQueries(0):
            create_extra_permissions(self.app_config, verbosity=0, apps=state.apps)
