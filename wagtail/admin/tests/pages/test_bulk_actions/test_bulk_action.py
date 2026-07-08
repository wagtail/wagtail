import swapper
from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils

page_app, page_model = swapper.split(
    swapper.get_model_name("wagtailcore", "Page").lower()
)


class TestBulkActionDispatcher(WagtailTestUtils, TestCase):
    def setUp(self):
        # Login
        self.user = self.login()

    def test_bulk_action_invalid_action(self):
        url = reverse(
            "wagtail_bulk_action",
            args=(
                page_app,
                page_model,
                "ships",
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_bulk_action_invalid_model(self):
        url = reverse(
            "wagtail_bulk_action",
            args=(
                "doesnotexist",
                "doesnotexist",
                "doesnotexist",
            ),
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
