from wagtail.coreutils import get_dummy_request
from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestGenericSetting


class GenericSettingsTestMixin:
    def setUp(self):
        root = Page.objects.first()
        other_root = Page(title="Other Root")
        root.add_child(instance=other_root)

        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(hostname="other", root_page=other_root)

        self.default_settings = TestGenericSetting.objects.create(
            title="Default GenericSettings title", email="email@example.com"
        )

    def get_request(self, site=None):
        if site is None:
            site = self.default_site
        return get_dummy_request(site=site)
