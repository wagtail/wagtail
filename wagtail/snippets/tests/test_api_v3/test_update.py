import json

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    AdvertWithCustomPrimaryKey,
    FullFeaturedSnippet,
    RevisableChildModel,
    UUIDSnippetWithRelations,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetUpdateBase(TestV3Base, WagtailTestUtils, TestCase):
    model = None

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def patch(self, pk, data, query_params=""):
        return self.client.patch(
            reverse(
                "wagtailapi_v3:update_snippet",
                kwargs={"type": self.model._meta.label, "pk": pk},
            )
            + f"?{query_params}",
            data=json.dumps(data),
            content_type="application/json",
        )


class TestV3SnippetUpdate(TestV3SnippetUpdateBase):
    model = Advert

    def setUp(self):
        super().setUp()
        self.advert = Advert.objects.create(text="Advert 1", url="https://wagtail.org")

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Unauthorized",
        )

    def test_superuser_can_update(self):
        response = self.patch(self.advert.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.advert.refresh_from_db()
        self.assertEqual(self.advert.text, "Updated")

    def test_update_with_quotable_pk(self):
        advert = AdvertWithCustomPrimaryKey.objects.create(
            advert_id=QUOTABLE_PK, text="Old text"
        )
        response = self.client.patch(
            reverse(
                "wagtailapi_v3:update_snippet",
                kwargs={
                    "type": "tests.AdvertWithCustomPrimaryKey",
                    "pk": quote(advert.pk),
                },
            ),
            data=json.dumps({"text": "New text"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        advert.refresh_from_db()
        self.assertEqual(advert.text, "New text")

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

    def test_meta_type_can_be_omitted(self):
        empty_metas = [
            {},
            {"meta": None},
            {"meta": {}},
            {"meta": {"type": "tests.Advert"}},
        ]
        for meta in empty_metas:
            with self.subTest(meta=meta):
                payload = {"text": "Updated", **meta}
                response = self.patch(self.advert.pk, payload)
                self.assertEqual(response.status_code, 200)
                self.advert.refresh_from_db()
                self.assertEqual(self.advert.text, "Updated")

    def test_malformed_meta_type_returns_422(self):
        problem_metas = [
            123,
            "not a dict",
            ["not", "a", "dict"],
            {"type": 123},
            {"type": ["not", "a", "string"]},
            {"type": "auth.User"},
            {"type": "tests.UUIDSnippetWithRelations"},
        ]
        for meta in problem_metas:
            with self.subTest(meta=meta):
                data = {"meta": meta, "text": "Updated"}
                response = self.patch(self.advert.pk, data)
                if isinstance(meta, dict):
                    self.assert_problem_response(
                        response,
                        status_code=422,
                        detail_contains="Validation failed",
                        errors=[
                            {
                                "type": "literal_error",
                                "loc": ["body", "meta", "type"],
                                "msg": "Input should be 'tests.Advert'",
                            }
                        ],
                    )
                else:
                    self.assert_problem_response(
                        response,
                        status_code=422,
                        detail_contains="Validation failed",
                        errors=[
                            {
                                "type": "dict_type",
                                "loc": ["body", "meta"],
                                "msg": "Input should be a valid dictionary",
                            }
                        ],
                    )
                self.advert.refresh_from_db()
                self.assertEqual(self.advert.text, "Advert 1")

    def test_action_is_silently_ignored(self):
        response = self.patch(
            self.advert.pk,
            {"meta": {"action": "publish"}, "text": "Updated"},
        )
        self.assertEqual(response.status_code, 200)
        self.advert.refresh_from_db()
        self.assert_log_actions(self.advert, ["wagtail.edit"])
        self.assertEqual(self.advert.text, "Updated")


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

    def test_update_with_streamfield(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello",
            feed_image=image,
            body=[{"type": "text", "value": "hello world"}],
        )
        response = self.patch(
            snippet.pk,
            {
                "feed_image_id": image.pk,
                "body": [{"type": "text", "value": "updated"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.body[0].value, "updated")

    def test_update_without_block_id_regenerates_it(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello",
            feed_image=image,
            body=[{"type": "text", "value": "original"}],
        )
        original_id = snippet.body[0].id
        response = self.patch(
            snippet.pk,
            {
                "feed_image_id": image.pk,
                "body": [{"type": "text", "value": "updated"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.body[0].value, "updated")
        self.assertNotEqual(snippet.body[0].id, original_id)

    def test_update_with_block_id_preserves_it(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello",
            feed_image=image,
            body=[{"type": "text", "value": "original"}],
        )
        original_id = snippet.body[0].id
        response = self.patch(
            snippet.pk,
            {
                "feed_image_id": image.pk,
                "body": [{"type": "text", "value": "updated", "id": original_id}],
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.body[0].value, "updated")
        self.assertEqual(snippet.body[0].id, original_id)

    def test_update_with_streamfield_diffing(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello",
            feed_image=image,
            body=[
                {"type": "text", "value": "first"},
                {"type": "text", "value": "second"},
                {"type": "text", "value": "third"},
            ],
        )
        first_id, second_id, third_id = (block.id for block in snippet.body)

        response = self.patch(
            snippet.pk,
            {
                "feed_image_id": image.pk,
                "body": [
                    {"type": "text", "value": "third updated", "id": third_id},
                    {"type": "text", "value": "first updated", "id": first_id},
                    {"type": "text", "value": "new block"},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(len(snippet.body), 3)
        self.assertEqual(snippet.body[0].value, "third updated")
        self.assertEqual(snippet.body[0].id, third_id)
        self.assertEqual(snippet.body[1].value, "first updated")
        self.assertEqual(snippet.body[1].id, first_id)
        self.assertEqual(snippet.body[2].value, "new block")
        self.assertNotIn(snippet.body[2].id, {first_id, second_id, third_id})

    def test_update_with_rich_text_block(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello",
            feed_image=image,
            body=[{"type": "rich_text", "value": "<p>original</p>"}],
        )
        response = self.patch(
            snippet.pk,
            {
                "feed_image_id": image.pk,
                "body": [{"type": "rich_text", "value": "<p>updated <b>text</b></p>"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertIn("updated <b>text</b>", str(snippet.body[0].value))

    def test_update_with_various_streamfield_block_types(self):
        original_image = Image.objects.create(
            title="Original image", file=get_test_image_file()
        )
        new_image = Image.objects.create(title="New image", file=get_test_image_file())
        cases = [
            (
                "product",
                {"name": "Original", "price": "1.00"},
                {"name": "Widget", "price": "9.99"},
                lambda value: (
                    self.assertEqual(value["name"], "Widget"),
                    self.assertEqual(value["price"], "9.99"),
                ),
                lambda value: self.assertEqual(
                    value, {"name": "Widget", "price": "9.99"}
                ),
            ),
            (
                "raw_html",
                "<div>original</div>",
                "<div>updated</div>",
                lambda value: self.assertEqual(str(value), "<div>updated</div>"),
                lambda value: self.assertEqual(value, "<div>updated</div>"),
            ),
            (
                "books",
                [{"type": "title", "value": "Original"}],
                [
                    {"type": "title", "value": "Dune"},
                    {"type": "author", "value": "Frank Herbert"},
                ],
                lambda value: (
                    self.assertEqual(value[0].value, "Dune"),
                    self.assertEqual(value[1].value, "Frank Herbert"),
                ),
                lambda value: (
                    self.assertTrue(all(item["id"] for item in value)),
                    self.assertEqual(
                        [
                            {k: v for k, v in item.items() if k != "id"}
                            for item in value
                        ],
                        [
                            {"type": "title", "value": "Dune"},
                            {"type": "author", "value": "Frank Herbert"},
                        ],
                    ),
                ),
            ),
            (
                "title_list",
                ["Original"],
                ["First", "Second", "Third"],
                lambda value: self.assertEqual(
                    list(value), ["First", "Second", "Third"]
                ),
                lambda value: self.assertEqual(value, ["First", "Second", "Third"]),
            ),
            (
                "image",
                original_image.pk,
                new_image.pk,
                lambda value: self.assertEqual(value.pk, new_image.pk),
                lambda value: self.assertEqual(value, new_image.pk),
            ),
            (
                "image_with_alt",
                {
                    "image": original_image.pk,
                    "decorative": False,
                    "alt_text": "Original alt",
                },
                {
                    "image": original_image.pk,
                    "decorative": False,
                    "alt_text": "Updated alt",
                },
                lambda value: self.assertEqual(
                    value.contextual_alt_text, "Updated alt"
                ),
                lambda value: self.assertEqual(
                    value,
                    {
                        "image": original_image.pk,
                        "decorative": False,
                        "alt_text": "Updated alt",
                    },
                ),
            ),
        ]
        for (
            block_type,
            original_value,
            updated_value,
            assert_db_value,
            assert_api_value,
        ) in cases:
            with self.subTest(block_type=block_type):
                snippet = UUIDSnippetWithRelations.objects.create(
                    text=f"Hello {block_type}",
                    feed_image=original_image,
                    body=[{"type": block_type, "value": original_value}],
                )
                response = self.patch(
                    snippet.pk,
                    {"body": [{"type": block_type, "value": updated_value}]},
                )
                self.assertEqual(response.status_code, 200)

                snippet.refresh_from_db()
                self.assertEqual(snippet.body[0].block_type, block_type)
                assert_db_value(snippet.body[0].value)

                [block] = response.json()["body"]
                self.assertEqual(block["type"], block_type)
                assert_api_value(block["value"])

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


class TestV3SnippetUpdateWithRichText(TestV3SnippetUpdateBase):
    model = UUIDSnippetWithRelations

    @classmethod
    def setUpTestData(cls):
        cls.snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello", rich_body="<p>original</p>"
        )

    def patch_rich_body(self, value, query_params=""):
        return self.patch(self.snippet.pk, {"rich_body": value}, query_params)

    def test_plain_string_stored_sanitised(self):
        response = self.patch_rich_body("<p><i>x</i></p><script>alert(1)</script>")
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertNotIn("<script", self.snippet.rich_body)
        self.assertIn("<i>x</i>", self.snippet.rich_body)

    def test_feature_restricted_field_strips_out_of_features(self):
        # bold/h2 are not enabled in rich_body features list
        response = self.patch_rich_body("<h2>T</h2><p><b>x</b></p>")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        meta = data["meta"]
        self.assertEqual(
            meta.get("warnings"),
            [
                {
                    "tag": "h2",
                    "action": "unwrapped",
                    "reason": "feature_disabled",
                    "attribute": None,
                    "detail": "<h2>T</h2>",
                },
                {
                    "tag": "b",
                    "action": "unwrapped",
                    "reason": "feature_disabled",
                    "attribute": None,
                    "detail": "<b>x</b>",
                },
            ],
        )
        self.snippet.refresh_from_db()
        self.assertNotIn("<h2>", self.snippet.rich_body)
        self.assertNotIn("<b>", self.snippet.rich_body)

    def test_envelope_stored_sanitised(self):
        response = self.patch_rich_body(
            {"format": "db_html", "content": "<p>hi <script>alert(1)</script></p>"}
        )
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertNotIn("<script", self.snippet.rich_body)
        self.assertIn("hi", self.snippet.rich_body)

    def test_entity_references_survive(self):
        response = self.patch_rich_body('<p><a linktype="page" id="2">home</a></p>')
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertIn('linktype="page"', self.snippet.rich_body)
        self.assertIn('id="2"', self.snippet.rich_body)

    def test_unknown_format_rejected(self):
        response = self.patch_rich_body({"format": "markdown", "content": "# Hi"})
        self.assert_problem_response(response, status_code=422)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.rich_body, "<p>original</p>")

    def test_rich_body_untouched_when_omitted(self):
        response = self.patch(self.snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.text, "Updated")
        self.assertEqual(self.snippet.rich_body, "<p>original</p>")

    def test_rich_body_cleared_with_empty_string(self):
        # The Draftail widget round-trip normalises the empty value to an
        # empty paragraph, so what gets stored is not "".
        response = self.patch_rich_body("")
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertRegex(
            self.snippet.rich_body,
            r'^<p data-block-key="[a-z0-9]+"></p>$',
        )

    def test_write_response_honours_format(self):
        # Write endpoints return the detail schema, so the format applies
        # there too.
        response = self.patch_rich_body(
            '<p><a linktype="page" id="2">home</a></p>',
            "rich_text_format=html",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("<a href=", response.json()["rich_body"])


class TestV3SnippetUpdateWithRichTextMarkdown(TestV3SnippetUpdateBase):
    model = UUIDSnippetWithRelations

    @classmethod
    def setUpTestData(cls):
        cls.snippet = UUIDSnippetWithRelations.objects.create(
            text="Hello", rich_body="<p>original</p>"
        )

    def patch_rich_body(self, content, rich_text_format="db_markdown"):
        return self.patch(
            self.snippet.pk,
            {"rich_body": {"format": rich_text_format, "content": content}},
        )

    def test_db_markdown_input_on_patch(self):
        response = self.patch_rich_body("*after*")
        self.assertEqual(response.status_code, 200, response.json())
        self.snippet.refresh_from_db()
        self.assertNotIn("original", self.snippet.rich_body)
        # italic is in the field's features, so *after* becomes <i> markup
        self.assertIn("<i>after</i>", self.snippet.rich_body)

    def test_malformed_reference_gives_422_with_field_and_line(self):
        response = self.patch_rich_body("[x](wagtail://page?id=abc)")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": [
                        "body",
                        "data",
                        "tests.UUIDSnippetWithRelations",
                        "rich_body",
                    ],
                    "msg": (
                        "Value error, Invalid Markdown in rich text at line 1: "
                        "Entity resolver failed for URL 'wagtail://page?id=abc': "
                        "invalid literal for int() with base 10: 'abc'"
                    ),
                }
            ],
        )
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.rich_body, "<p>original</p>")

    def test_wagtail_ref_without_id_gives_422(self):
        # A wagtail:// reference missing its id must fail validation, never 500.
        response = self.patch_rich_body("[x](wagtail://page)")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "value_error",
                    "loc": [
                        "body",
                        "data",
                        "tests.UUIDSnippetWithRelations",
                        "rich_body",
                    ],
                    "msg": (
                        "Value error, Invalid Markdown in rich text: "
                        "wagtail://page reference requires id"
                    ),
                }
            ],
        )
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.rich_body, "<p>original</p>")


class TestV3SnippetUpdateWithDraftState(TestV3SnippetUpdateBase):
    """meta.action support for DraftStateMixin snippets."""

    model = FullFeaturedSnippet

    def setUp(self):
        super().setUp()
        self.snippet = FullFeaturedSnippet.objects.create(
            text="Original", some_number=1, live=False
        )

    def test_update_with_publish_action_publishes(self):
        response = self.patch(
            self.snippet.pk, {"meta": {"action": "publish"}, "text": "Updated"}
        )
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertTrue(self.snippet.live)
        self.assertEqual(self.snippet.text, "Updated")
        self.assertIsNotNone(self.snippet.live_revision)
        self.assertEqual(
            self.snippet.live_revision_id, self.snippet.get_latest_revision().pk
        )

    def test_user_with_change_but_not_publish_permission_with_publish_action(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(
            Permission.objects.get(codename="change_fullfeaturedsnippet")
        )
        self.login(username="changer", password="password")
        response = self.patch(
            self.snippet.pk, {"meta": {"action": "publish"}, "text": "Updated"}
        )
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to publish this full-featured snippet."
            ),
        )

        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.text, "Original")
        self.assertFalse(self.snippet.live)
        self.assertFalse(self.snippet.has_unpublished_changes)
        self.assertEqual(self.snippet.revisions.count(), 0)
        self.assert_log_actions(self.snippet, [])

    def test_update_without_action_does_not_publish(self):
        response = self.patch(self.snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertFalse(self.snippet.live)
        self.assertIsNone(self.snippet.live_revision)

    def test_update_with_invalid_action_returns_422(self):
        response = self.patch(
            self.snippet.pk,
            {"meta": {"action": "not_a_real_action"}, "text": "Updated"},
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "literal_error",
                    "loc": [
                        "body",
                        "data",
                        "tests.FullFeaturedSnippet",
                        "meta",
                        "action",
                    ],
                    "msg": "Input should be 'publish'",
                }
            ],
        )

    def test_update_saves_one_revision_and_logs_edit(self):
        response = self.patch(self.snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.revisions.count(), 1)
        self.assert_log_actions(self.snippet, ["wagtail.edit"])

    def test_update_of_live_snippet_does_not_touch_live_row_until_published(self):
        self.snippet.live = True
        self.snippet.save()
        self.snippet.save_revision().publish()

        response = self.patch(self.snippet.pk, {"text": "New Draft Text"})
        self.assertEqual(response.status_code, 200)

        snippet = FullFeaturedSnippet.objects.get(pk=self.snippet.pk)
        self.assertTrue(snippet.live)
        self.assertEqual(snippet.text, "Original")

        latest_revision = snippet.get_latest_revision()
        self.assertNotEqual(snippet.live_revision_id, latest_revision.pk)
        self.assertEqual(latest_revision.content["text"], "New Draft Text")

        latest_revision.publish()
        snippet.refresh_from_db()
        self.assertEqual(snippet.text, "New Draft Text")


class TestV3SnippetUpdateWhenLocked(TestV3SnippetUpdateBase):
    model = FullFeaturedSnippet

    @classmethod
    def setUpTestData(cls):
        cls.snippet = FullFeaturedSnippet.objects.create(
            text="Original", some_number=1, live=False
        )

    def test_update_when_locked_is_rejected(self):
        # Lock with no locked_by (e.g. locked by a script): applies to everyone
        self.snippet.locked = True
        self.snippet.save()

        logs_since = timezone.now()
        response = self.patch(self.snippet.pk, {"text": "Updated"})
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "The full-featured snippet could not be saved as it is locked."
            ),
        )

        # Nothing was saved, no change, no draft/revision/log entry
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.text, "Original")
        self.assertFalse(self.snippet.has_unpublished_changes)
        self.assertEqual(self.snippet.revisions.count(), 0)
        self.assert_log_actions(self.snippet, [], since=logs_since)

    def test_update_when_locked_by_self_is_allowed(self):
        self.snippet.locked = True
        self.snippet.locked_by = self.user
        self.snippet.locked_at = timezone.now()
        self.snippet.save()

        response = self.patch(self.snippet.pk, {"text": "Updated"})
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.text, "Updated")


class TestV3SnippetUpdateWithPermissionedFields(TestV3SnippetUpdateBase):
    model = RevisableChildModel

    @classmethod
    def setUpTestData(cls):
        cls.snippet = RevisableChildModel.objects.create(
            text="Hello", secret_text="original"
        )

    def test_superuser_can_update_secret_text(self):
        response = self.patch(self.snippet.pk, {"secret_text": "updated"})
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.secret_text, "updated")

    def test_user_with_change_permission_cannot_update_secret_text(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(
            Permission.objects.get(codename="change_revisablechildmodel")
        )
        self.login(user)
        response = self.patch(
            self.snippet.pk,
            {"text": "Updated", "secret_text": "should be ignored"},
        )
        self.assertEqual(response.status_code, 200)
        self.snippet.refresh_from_db()
        # secret_text was dropped from the form for this user, so it is
        # left untouched while the non-protected field updates normally
        self.assertEqual(self.snippet.text, "Updated")
        self.assertEqual(self.snippet.secret_text, "original")
