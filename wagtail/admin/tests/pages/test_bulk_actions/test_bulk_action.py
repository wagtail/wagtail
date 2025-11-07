from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils


class TestBulkActionDispatcher(WagtailTestUtils, TestCase):
    def setUp(self):
        # Login
        self.user = self.login()

    def test_bulk_action_invalid_action(self):
        url = reverse(
            "wagtail_bulk_action",
            args=(
                "wagtailcore",
                "page",
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

    def test_bulk_action_preserves_all_filter_query_parameters(self):
        home_page = Page.objects.get(id=2)

        draft1 = home_page.add_child(instance=Page(title="Draft 1", slug="draft-1"))
        draft1.save_revision()
        draft2 = home_page.add_child(instance=Page(title="Draft 2", slug="draft-2"))
        draft2.save_revision()

        filters = {
            "content_type": draft1.content_type_id,  
            "q": "draft",                            
            "status": "draft",                      
            "p": "3",                              
        }

        query = (
            f"id={draft1.id}&id={draft2.id}"         
            f"&action=publish"                       
            f"&next=/admin/pages/"                   
            + "".join(f"&{key}={value}" for key, value in filters.items())  
        )

        url = reverse("wagtail_bulk_action", args=("wagtailcore", "page", "publish")) + "?" + query
        response = self.client.post(url, follow=True)

        final_url = response.redirect_chain[-1][0]

        for key, value in filters.items():
            self.assertIn(f"{key}={value}", final_url, msg=f"Filter {key} was lost")

        self.assertNotIn("id=", final_url)
        self.assertNotIn("action=", final_url)
        self.assertNotIn("next=", final_url)

        
        