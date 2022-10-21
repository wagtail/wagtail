from django.http import HttpRequest

from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestGenericSetting


class GenericSettingsTestMixin:
    @classmethod
    def setUpTestData(cls):
        root = Page.objects.first()
        other_root = Page(title="Other Root")
        root.add_child(instance=other_root)

        cls.default_site = Site.objects.get(is_default_site=True)
        cls.other_site = Site.objects.create(hostname="other", root_page=other_root)

        cls.default_settings = TestGenericSetting.objects.create(
            title="Default GenericSettings title", email="email@example.com"
        )

    def get_request(self, site=None):
        if site is None:
            site = self.default_site
        request = HttpRequest()
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port
        return request
