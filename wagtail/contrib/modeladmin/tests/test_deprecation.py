from django.apps import apps
from django.test import SimpleTestCase


class TestDeprecationWarning(SimpleTestCase):
    def test_deprecation_warning(self):
        config = apps.get_app_config("wagtailmodeladmin")
        with self.assertWarnsMessage(
            DeprecationWarning,
            "wagtail.contrib.modeladmin is deprecated. "
            "Use wagtail.snippets or the separate wagtail-modeladmin package instead.",
        ):
            config.ready()
