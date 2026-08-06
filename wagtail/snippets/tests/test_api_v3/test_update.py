import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.testapp.models import Advert, UUIDSnippetWithRelations
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetUpdateBase(TestV3Base, WagtailTestUtils, TestCase):
    model = None

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def patch(self, pk, data):
        return self.client.patch(
            reverse(
                "wagtailapi_v3:update_snippet",
                kwargs={"type": self.model._meta.label, "pk": pk},
            ),
            data=json.dumps(data),
            content_type="application/json",
        )


class TestV3SnippetUpdate(TestV3SnippetUpdateBase):
    model = Advert

    def setUp(self):
        super().setUp()
        self.advert = Advert.objects.create(text="Advert 1", url="https://wagtail.org")

    def test_anonymous_returns_401(self):
        self.client.logout()
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Authentication required",
        )

    def test_superuser_can_update(self):
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.advert.refresh_from_db()
        self.assertEqual(self.advert.text, "Updated")

    def test_partial_update_leaves_other_fields_unchanged(self):
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.advert.refresh_from_db()
        self.assertEqual(self.advert.url, "https://wagtail.org")

    def test_user_without_change_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_user_with_change_permission_can_update(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="change_advert"))
        self.login(username="changer", password="password")
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)

    def test_unknown_pk_returns_404(self):
        response = self.patch(999999, {"text": "Updated"})
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Advert matches the given query.",
        )

    def test_logs_edit_action(self):
        self.patch(self.advert.pk, {"text": "Updated"})
        self.assert_log_actions(self.advert, ["wagtail.edit"])

    def test_update_with_unknown_field_ignores_it(self):
        response = self.patch(self.advert.pk, {"not_a_real_field": "ignored"})
        self.assertEqual(response.status_code, 200)


class TestV3SnippetUpdateWithRelations(TestV3SnippetUpdateBase):
    model = UUIDSnippetWithRelations

    def test_omitted_non_blank_extra_field_does_not_fail_validation(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(text="Original")
        response = self.patch(snippet.pk, {"feed_image_id": image.pk})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.text, "Original")
        self.assertEqual(snippet.feed_image_id, image.pk)

    def test_omitted_field_is_left_untouched(self):
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Original", subtitle="", intro="the intro"
        )
        response = self.patch(snippet.pk, {"text": "New title"})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.text, "New title")
        self.assertEqual(snippet.intro, "the intro")

    def test_update_with_non_writable_api_field_ignores_it(self):
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Original", subtitle="Original subtitle"
        )
        response = self.patch(snippet.pk, {"subtitle": "should be ignored"})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.subtitle, "Original subtitle")

    def test_update_with_foreign_key_field(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        response = self.patch(snippet.pk, {"feed_image_id": image.pk})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.feed_image_id, image.pk)

    def test_update_with_foreign_key_field_omitted_is_untouched(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello", feed_image=image
        )
        response = self.patch(snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.feed_image_id, image.pk)

    def test_update_with_foreign_key_field_set_to_null_clears_it(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello", feed_image=image
        )
        response = self.patch(snippet.pk, {"feed_image_id": None})
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertIsNone(snippet.feed_image_id)

    def test_update_with_child_relations_replaces_them(self):
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        snippet.sections.create(caption="Old", link_external="http://example.com/old")
        snippet.save()
        response = self.patch(
            snippet.pk,
            {
                "sections": [
                    {"caption": "New", "link_external": "http://example.com/new"}
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet = UUIDSnippetWithRelations.objects.get(pk=snippet.pk)
        sections = list(snippet.sections.all())
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].caption, "New")

    def test_update_with_child_relation_id_edits_in_place(self):
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        item = snippet.sections.create(
            caption="Old", link_external="http://example.com/old"
        )
        snippet.save()
        response = self.patch(
            snippet.pk,
            {
                "sections": [
                    {
                        "id": item.pk,
                        "caption": "Edited",
                        "link_external": "http://example.com/old",
                    }
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet = UUIDSnippetWithRelations.objects.get(pk=snippet.pk)
        sections = list(snippet.sections.all())
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].pk, item.pk)
        self.assertEqual(sections[0].caption, "Edited")

    def test_update_with_child_relation_unknown_id_is_treated_as_new(self):
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        item = snippet.sections.create(
            caption="Old", link_external="http://example.com/old"
        )
        snippet.save()
        response = self.patch(
            snippet.pk,
            {
                "sections": [
                    {
                        "id": item.pk + 999,
                        "caption": "New",
                        "link_external": "http://example.com/new",
                    }
                ]
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet = UUIDSnippetWithRelations.objects.get(pk=snippet.pk)
        sections = list(snippet.sections.all())
        self.assertEqual(len(sections), 1)
        self.assertNotEqual(sections[0].pk, item.pk)
        self.assertNotEqual(sections[0].pk, item.pk + 999)
        self.assertEqual(sections[0].caption, "New")

    def test_child_relations_untouched_when_omitted(self):
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        snippet.sections.create(caption="Kept", link_external="http://example.com/kept")
        snippet.save()
        response = self.patch(snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        snippet = UUIDSnippetWithRelations.objects.get(pk=snippet.pk)
        sections = list(snippet.sections.all())
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].caption, "Kept")

    def test_update_with_child_relation_new_item_via_document_fk(self):
        document = Document.objects.create(title="Test document")
        snippet = UUIDSnippetWithRelations.objects.create(text="Hello")
        response = self.patch(
            snippet.pk,
            {"sections": [{"caption": "Sec", "link_document_id": document.pk}]},
        )
        self.assertEqual(response.status_code, 200)
        snippet = UUIDSnippetWithRelations.objects.get(pk=snippet.pk)
        section = snippet.sections.get()
        self.assertEqual(section.link_document_id, document.pk)

    def test_unknown_pk_returns_404(self):
        response = self.patch(
            "00000000-0000-0000-0000-000000000000", {"text": "Updated"}
        )
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No UUIDSnippetWithRelations matches the given query.",
        )
