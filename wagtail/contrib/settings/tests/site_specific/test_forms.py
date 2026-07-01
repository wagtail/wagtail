from django.test import TestCase

from wagtail.contrib.settings.forms import SiteSwitchForm
from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestSiteSetting


class TestSiteSwitchFormOrdering(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(pk=2)
        Site.objects.all().delete()  # Drop the initial site.

    def _create_sites(self):
        # Standard site
        site_1 = Site.objects.create(hostname="charly.com", root_page=self.root_page)
        # Site with default
        site_2 = Site.objects.create(
            hostname="bravo.com", root_page=self.root_page, is_default_site=True
        )
        # Site with name
        site_3 = Site.objects.create(
            hostname="alfa.com", site_name="AAA Website", root_page=self.root_page
        )
        # Site with non-standard port
        site_4 = Site.objects.create(
            hostname="alfa.com", port=5678, root_page=self.root_page
        )
        return site_1, site_2, site_3, site_4

    def test_site_order_by_site_name_and_hostname(self):
        site_1, site_2, site_3, site_4 = self._create_sites()
        form = SiteSwitchForm(site_1, TestSiteSetting, sites=Site.objects.all())
        expected_choices = [
            (f"/admin/settings/tests/testsitesetting/{site_3.id}/", "AAA Website"),
            (f"/admin/settings/tests/testsitesetting/{site_4.id}/", "alfa.com:5678"),
            (
                f"/admin/settings/tests/testsitesetting/{site_2.id}/",
                "bravo.com [default]",
            ),
            (f"/admin/settings/tests/testsitesetting/{site_1.id}/", "charly.com"),
        ]
        self.assertEqual(form.fields["site"].choices, expected_choices)
