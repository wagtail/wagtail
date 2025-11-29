from django.test import TestCase

from wagtail.contrib.settings.forms import SiteSwitchForm
from wagtail.models import Page, Site
from wagtail.test.testapp.models import TestSiteSetting


class TestSiteSwitchFormOptions(TestCase):
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
            hostname="alfa.com", site_name="Alfa Website", root_page=self.root_page
        )
        # Site with non-standard port
        site_4 = Site.objects.create(
            hostname="alfa.com", port=5678, root_page=self.root_page
        )
        return site_1, site_2, site_3, site_4

    def test_all_sites_are_available_as_options(self):
        site_1, site_2, site_3, site_4 = self._create_sites()
        form = SiteSwitchForm(site_1, TestSiteSetting, sites=Site.objects.all())

        # Build the set of choice URLs present in the form
        choice_urls = {value for value, label in form.fields["site"].choices}
        expected_urls = {
            f"/admin/settings/tests/testsitesetting/{site_1.id}/",
            f"/admin/settings/tests/testsitesetting/{site_2.id}/",
            f"/admin/settings/tests/testsitesetting/{site_3.id}/",
            f"/admin/settings/tests/testsitesetting/{site_4.id}/",
        }

        self.assertEqual(choice_urls, expected_urls)

    def test_site_str_used_for_option_labels(self):
        site_1, site_2, site_3, site_4 = self._create_sites()
        form = SiteSwitchForm(site_1, TestSiteSetting, sites=Site.objects.all())

        # Map site id (from URL) to label and assert it matches str(site)
        label_by_id = {}
        for value, label in form.fields["site"].choices:
            # value looks like "/admin/settings/tests/testsitesetting/<id>/"
            site_id = int(value.rstrip("/").split("/")[-1])
            label_by_id[site_id] = label

        for site in (site_1, site_2, site_3, site_4):
            self.assertEqual(label_by_id[site.id], str(site))
