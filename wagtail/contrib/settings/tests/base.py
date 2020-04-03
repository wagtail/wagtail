from django.http import HttpRequest
from wagtail.core.models import Page, Site
from wagtail.tests.testapp.models import TestSetting


class SettingsTestMixin:

    def setUp(self):
        root = Page.objects.first()
        other_home = Page(title='Other Root')
        root.add_child(instance=other_home)

        self.default_site = Site.objects.get(is_default_site=True)
        self.default_site_settings = TestSetting.objects.create(
            title='Site title',
            email='initial@example.com',
            site=self.default_site)

        self.other_site = Site.objects.create(hostname='other', root_page=other_home)
        self.other_site_settings = TestSetting.objects.create(
            title='Other title',
            email='other@other.com',
            site=self.other_site)

    def get_request(self, site=None):
        if site is None:
            site = self.default_site
        request = HttpRequest()
        request.META['HTTP_HOST'] = site.hostname
        request.META['SERVER_PORT'] = site.port
        return request
