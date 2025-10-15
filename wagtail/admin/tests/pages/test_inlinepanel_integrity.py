from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.testapp.models import ArticlePage, Tag
from wagtail.test.utils import WagtailTestUtils


class InlinePanelIntegrityTest(TestCase, WagtailTestUtils):
    def setUp(self):
        self.login()
        self.root = Page.get_first_root_node()

        self.page = self.root.add_child(
            instance=ArticlePage(title="Article", slug="article")
        )
        self.page.save_revision().publish()

    def test_unpublish_resave_causes_integrity_error(self):
        tag = Tag.objects.create(title="Demo", slug="demo")

        response = self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)),
            {
                "title": "Article",
                "slug": "article",
                "tags-TOTAL_FORMS": "1",
                "tags-INITIAL_FORMS": "0",
                "tags-MIN_NUM_FORMS": "0",
                "tags-MAX_NUM_FORMS": "1000",
                "tags-0-id": "",
                "tags-0-tag": tag.id,
                "action-publish": "Publish",
            },
        )
        self.assertEqual(response.status_code, 302)

        self.client.post(
            reverse("wagtailadmin_pages:unpublish", args=(self.page.id,)),
            {"action-unpublish": "Unpublish"},
        )

        tagged_item = self.page.tags.first()

        self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.page.id,)),
            {
                "title": "Article",
                "slug": "article",
                "tags-TOTAL_FORMS": "1",
                "tags-INITIAL_FORMS": "1",
                "tags-MIN_NUM_FORMS": "0",
                "tags-MAX_NUM_FORMS": "1000",
                "tags-0-id": str(tagged_item.id),
                "tags-0-tag": tag.id,
                "tags-0-ORDER": "1",
                "action-publish": "Publish",
            },
        )

        self.assertEqual(
            self.page.tags.count(),
            1,
            "Tag should not duplicate after unpublishing + resaving",
        )
