from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from wagtail.documents import get_document_model
from wagtail.documents.tests.utils import get_test_document_file
from wagtail.models import Collection
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils

Document = get_document_model()


class TestDocumentBulkDeleteViewWithFilters(
    AdminTemplateTestUtils, WagtailTestUtils, TestCase
):
    @classmethod
    def setUpTestData(cls):
        cls.collection = Collection.get_first_root_node().add_child(
            name="Test collection"
        )
        cls.doc = Document.objects.create(
            title="Test document",
            file=get_test_document_file(),
            collection=cls.collection,
        )

    def setUp(self):
        self.login()
        self.index_url = reverse("wagtaildocs:index")
        self.pagination = {"p": 2}
        self.filters = {"collection_id": self.collection.id}
        self.params = {**self.filters, **self.pagination}
        self.bulk_url = reverse(
            "wagtail_bulk_action",
            args=(Document._meta.app_label, Document._meta.model_name, "delete"),
        )
        self.expected_url = self.index_url + "?" + urlencode(self.params, doseq=True)

    def test_listing_page_buttons_preserve_filters(self):
        resp = self.client.get(self.index_url, self.params)
        self.assertEqual(resp.status_code, 200)

        soup = self.get_soup(resp.content)
        link = soup.select_one(f'a[href^="{self.bulk_url}"][data-bulk-action-button]')
        self.assertIsNotNone(link, "bulk delete link not found")

        href = link["href"]
        self.assertIn(
            urlencode({"next": self.expected_url}, doseq=True),
            href,
            "link 'next' is not the filtered URL",
        )

    def test_confirmation_view_preserves_filters(self):
        url_params = {"next": self.index_url, "id": self.doc.id, **self.params}
        url = self.bulk_url + "?" + urlencode(url_params, doseq=True)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(
            resp, "wagtailadmin/bulk_actions/confirmation/form.html"
        )

        self.assertEqual(resp.context["next"], self.expected_url)

        soup = self.get_soup(resp.content)

        hidden_next = soup.select_one('form input[type="hidden"][name="next"]')
        self.assertIsNotNone(hidden_next)
        self.assertEqual(hidden_next["value"], self.expected_url)

        cancel = soup.select_one(f'form a[href="{self.expected_url}"]')
        self.assertIsNotNone(cancel)

    def test_post_preserves_filters(self):
        url_params = {"next": self.index_url, "id": self.doc.id, **self.params}
        url = self.bulk_url + "?" + urlencode(url_params, doseq=True)

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, self.expected_url, fetch_redirect_response=False)

        self.assertFalse(Document.objects.filter(pk=self.doc.pk).exists())
