from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailTestUtils


class TestPageListingQueryOptimizations(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.root_page = Page.objects.get(id=2)

    def test_page_listing_query_count_with_site_filter(self):
        url = reverse(
            "wagtailadmin_explore",
            args=(self.root_page.id,),
        )

        self.client.get(url)

        site = Site.objects.first()

        with self.assertNumQueries(21):
            self.client.get(url, {"site": [site.pk]})
