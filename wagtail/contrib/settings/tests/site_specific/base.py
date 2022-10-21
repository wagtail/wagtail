from django.http import HttpRequest

from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestSiteSetting


class SiteSettingsTestMixin:
    @classmethod
    def setUpTestData(cls):
        root = Page.objects.first()
        other_home = Page(title="Other Root")
        root.add_child(instance=other_home)

        cls.default_site = Site.objects.get(is_default_site=True)
        cls.default_settings = TestSiteSetting.objects.create(
            title="Site title", email="initial@example.com", site=cls.default_site
        )

        cls.other_site = Site.objects.create(hostname="other", root_page=other_home)
        cls.other_settings = TestSiteSetting.objects.create(
            title="Other title", email="other@other.com", site=cls.other_site
        )

    def get_request(self, site=None):
        if site is None:
            site = self.default_site
        request = HttpRequest()
        request.META["HTTP_HOST"] = site.hostname
        request.META["SERVER_PORT"] = site.port
        return request
