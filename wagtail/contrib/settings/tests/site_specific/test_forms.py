from django.test import TestCase

from wagtail.contrib.settings.forms import SiteSwitchForm
from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestSiteSetting


class TestSiteSwitchFromSiteOrdering(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(pk=2)
        Site.objects.all().delete()  # Drop the initial site.

    def test_site_order_by_hostname(self):
        site_1 = Site.objects.create(hostname="charly.com", root_page=self.root_page)
        site_2 = Site.objects.create(
            hostname="bravo.com", root_page=self.root_page, is_default_site=True
        )
        site_3 = Site.objects.create(hostname="alfa.com", root_page=self.root_page)
        form = SiteSwitchForm(site_1, TestSiteSetting)
        expected_choices = [
            (f"/admin/settings/tests/testsitesetting/{site_3.id}/", "alfa.com"),
            (
                f"/admin/settings/tests/testsitesetting/{site_2.id}/",
                "bravo.com [default]",
            ),
            (
                f"/admin/settings/tests/testsitesetting/{site_1.id}/",
                "charly.com",
            ),
        ]
        self.assertEqual(form.fields["site"].choices, expected_choices)
