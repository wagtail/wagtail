import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.testapp.models import (
    Advert,
    FullFeaturedSnippet,
    RevisableChildModel,
    UUIDSnippetWithRelations,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetCreateBase(TestV3Base, WagtailTestUtils, TestCase):
    model = None

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def post(self, data, query_params=""):
        return self.client.post(
            reverse(
                "wagtailapi_v3:create_snippet",
                kwargs={"type": self.model._meta.label},
            )
            + f"?{query_params}",
            data=json.dumps(data),
            content_type="application/json",
        )


class TestV3SnippetCreate(TestV3SnippetCreateBase):
    model = Advert

    def setUp(self):
        super().setUp()
        self.valid_payload = {"text": "New advert", "url": "https://wagtail.org"}

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.post(self.valid_payload)
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Unauthorized",
        )

    def test_superuser_can_create(self):
        initial_count = Advert.objects.count()
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Advert.objects.count(), initial_count + 1)
        content = response.json()
        self.assertEqual(set(content.keys()), {"id", "url", "text", "tags", "meta"})
        self.assertEqual(content["text"], "New advert")

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.post(self.valid_payload)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_user_with_add_permission_can_create(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(Permission.objects.get(codename="add_advert"))
        self.login(user)
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)

    def test_missing_required_field_returns_422(self):
        response = self.post({"url": "https://wagtail.org"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "missing",
                    "loc": ["body", "data", "tests.Advert", "text"],
                    "msg": "Field required",
                }
            ],
        )

    def test_logs_create_action(self):
        response = self.post(self.valid_payload)
        advert = Advert.objects.get(pk=response.json()["id"])
        self.assert_log_actions(advert, ["wagtail.create"])

    def test_create_with_unknown_field_ignores_it(self):
        response = self.post({**self.valid_payload, "not_a_real_field": "ignored"})
        self.assertEqual(response.status_code, 201)

    def test_meta_type_can_be_omitted(self):
        empty_metas = [
            {},
            {"meta": None},
            {"meta": {}},
            {"meta": {"type": "tests.Advert"}},
        ]
        for meta in empty_metas:
            with self.subTest(meta=meta):
                payload = {**self.valid_payload, **meta}
                response = self.post(payload)
                self.assertEqual(response.status_code, 201)

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
                data = {**self.valid_payload, "meta": meta}
                response = self.post(data)
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

    def test_action_is_silently_ignored(self):
        response = self.post({"meta": {"action": "publish"}, "text": "New advert"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Advert.objects.get(text="New advert").text, "New advert")


class TestV3SnippetCreateWithRelations(TestV3SnippetCreateBase):
    """FK, StreamField, and child-relation coverage Advert can't exercise."""

    model = UUIDSnippetWithRelations

    def test_create_with_uuid_primary_key(self):
        response = self.post({"text": "Hello"})
        self.assertEqual(response.status_code, 201)
        content = response.json()
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(content["uuid"], str(snippet.pk))
        self.assertNotIn("id", content)

    def test_create_with_foreign_key_field(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.post({"text": "Hello", "feed_image_id": image.pk})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(snippet.feed_image_id, image.pk)

    def test_create_with_foreign_key_field_omitted_is_null(self):
        response = self.post({"text": "Hello"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertIsNone(snippet.feed_image_id)

    def test_create_with_unknown_foreign_key_id_returns_422(self):
        response = self.post({"text": "Hello", "feed_image_id": 999999})
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[
                {
                    "type": "invalid_choice",
                    "loc": ["feed_image"],
                    "msg": (
                        "Select a valid choice. That choice is not one of "
                        "the available choices."
                    ),
                }
            ],
        )

    def test_create_with_streamfield(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.post(
            {
                "text": "Hello",
                "feed_image_id": image.pk,
                "body": [{"type": "text", "value": "hello world"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(len(snippet.body), 1)
        self.assertEqual(snippet.body[0].block_type, "text")
        self.assertEqual(snippet.body[0].value, "hello world")

    def test_create_with_various_streamfield_block_types(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        cases = [
            (
                "text",
                "hello streamfield",
                lambda value: self.assertEqual(value, "hello streamfield"),
                lambda value: self.assertEqual(value, "hello streamfield"),
            ),
            (
                "product",
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
                "<div>raw</div>",
                lambda value: self.assertEqual(str(value), "<div>raw</div>"),
                lambda value: self.assertEqual(value, "<div>raw</div>"),
            ),
            (
                "books",
                [
                    {"type": "title", "value": "Dune"},
                    {"type": "author", "value": "Frank Herbert"},
                ],
                lambda value: (
                    self.assertEqual(value[0].block_type, "title"),
                    self.assertEqual(value[0].value, "Dune"),
                    self.assertEqual(value[1].block_type, "author"),
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
                ["First", "Second", "Third"],
                lambda value: self.assertEqual(
                    list(value), ["First", "Second", "Third"]
                ),
                lambda value: self.assertEqual(value, ["First", "Second", "Third"]),
            ),
            (
                "image",
                image.pk,
                lambda value: self.assertEqual(value.pk, image.pk),
                lambda value: self.assertEqual(value, image.pk),
            ),
            (
                "image_with_alt",
                {
                    "image": image.pk,
                    "decorative": False,
                    "alt_text": "A test image",
                },
                lambda value: (
                    self.assertEqual(value.pk, image.pk),
                    self.assertEqual(value.contextual_alt_text, "A test image"),
                ),
                lambda value: self.assertEqual(
                    value,
                    {
                        "image": image.pk,
                        "decorative": False,
                        "alt_text": "A test image",
                    },
                ),
            ),
        ]
        for block_type, input_value, assert_db_value, assert_api_value in cases:
            with self.subTest(block_type=block_type):
                text = f"Hello {block_type}"
                response = self.post(
                    {
                        "text": text,
                        # UUIDSnippetWithRelationsAPIForm.clean() requires
                        # feed_image whenever body is given.
                        "feed_image_id": image.pk,
                        "body": [{"type": block_type, "value": input_value}],
                    }
                )
                self.assertEqual(response.status_code, 201)

                snippet = UUIDSnippetWithRelations.objects.get(text=text)
                self.assertEqual(snippet.body[0].block_type, block_type)
                assert_db_value(snippet.body[0].value)

                [block] = response.json()["body"]
                self.assertEqual(block["type"], block_type)
                self.assertTrue(block["id"])
                assert_api_value(block["value"])

    def test_create_with_rich_text_block(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.post(
            {
                "text": "Hello",
                "feed_image_id": image.pk,
                "body": [{"type": "rich_text", "value": "<p>hello <b>world</b></p>"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(snippet.body[0].block_type, "rich_text")
        self.assertIn("hello <b>world</b>", str(snippet.body[0].value))

    def test_create_with_invalid_streamfield_block_type_returns_422(self):
        response = self.post(
            {
                "text": "Hello",
                "body": [{"type": "not_a_real_block", "value": "x"}],
            }
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[{"msg": "body: unrecognised block type 'not_a_real_block'"}],
        )

    def test_create_with_child_relations(self):
        document = Document.objects.create(title="Test document")
        response = self.post(
            {
                "text": "Hello",
                "sections": [
                    {"caption": "First", "link_external": "http://example.com/1"},
                    {"caption": "Second", "link_document_id": document.pk},
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        sections = list(snippet.sections.order_by("pk"))
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].caption, "First")
        self.assertEqual(sections[1].link_document_id, document.pk)

    def test_create_with_child_relation_missing_link_returns_422(self):
        response = self.post(
            {
                "text": "Hello",
                "sections": [{"caption": "No link"}],
            }
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[
                {
                    "type": "invalid",
                    "loc": ["sections", 0, "__all__"],
                    "msg": "You must provide a related document or an external URL",
                }
            ],
        )


class TestV3SnippetCreateWithRelationsFieldFiltering(TestV3SnippetCreateBase):
    """api_fields writability edge cases, plus an api_base_form_class validator."""

    model = UUIDSnippetWithRelations

    def test_create_with_non_writable_api_field_ignores_it(self):
        response = self.post({"text": "Hello", "subtitle": "should be ignored"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(snippet.subtitle, "")

    def test_create_with_field_not_in_api_fields_ignores_it(self):
        response = self.post({"text": "Hello", "intro": "should be ignored"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(snippet.intro, "")

    def test_create_with_non_model_field_in_api_fields_ignores_it(self):
        response = self.post({"text": "Hello", "display_text": "should be ignored"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertEqual(snippet.display_text, "Hello")

    def test_create_with_non_writable_api_field_in_inline_model_ignores_it(self):
        response = self.post(
            {
                "text": "Hello",
                "sections": [
                    {
                        "caption": "First",
                        "link_external": "http://example.com",
                        "internal_note": "should be ignored",
                    }
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        section = snippet.sections.get()
        self.assertEqual(section.internal_note, "")

    def test_create_with_rich_text_field(self):
        response = self.post({"text": "Hello", "rich_body": "<p>hello</p>"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertIn("hello", snippet.rich_body)

    def test_api_base_form_class(self):
        # Requires feed_image whenever body is given - see
        # UUIDSnippetWithRelationsAPIForm.clean().
        response = self.post(
            {"text": "Hello", "body": [{"type": "text", "value": "hi"}]}
        )
        self.assert_problem_response(
            response,
            status_code=422,
            errors=[
                {
                    "type": "invalid",
                    "loc": ["feed_image"],
                    "msg": "This field is required when body is given.",
                }
            ],
        )


class TestV3SnippetCreateWithRichText(TestV3SnippetCreateBase):
    model = UUIDSnippetWithRelations

    def create_snippet(self, value, query_params=""):
        return self.post({"text": "Hello", "rich_body": value}, query_params)

    def test_plain_string_stored_sanitised(self):
        response = self.create_snippet("<p><i>x</i></p><script>alert(1)</script>")
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertNotIn("<script", snippet.rich_body)
        self.assertIn("<i>x</i>", snippet.rich_body)

    def test_feature_restricted_field_strips_out_of_features(self):
        # bold/h2 are not enabled in rich_body features list
        response = self.create_snippet("<h2>T</h2><p><b>x</b></p>")
        self.assertEqual(response.status_code, 201)
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
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertNotIn("<h2>", snippet.rich_body)
        self.assertNotIn("<b>", snippet.rich_body)

    def test_envelope_stored_sanitised(self):
        body = {"format": "db_html", "content": "<p>hi <script>alert(1)</script></p>"}
        response = self.create_snippet(body)
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertNotIn("<script", snippet.rich_body)
        self.assertIn("hi", snippet.rich_body)

    def test_entity_references_survive(self):
        response = self.create_snippet('<p><a linktype="page" id="2">home</a></p>')
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertIn('linktype="page"', snippet.rich_body)
        self.assertIn('id="2"', snippet.rich_body)

    def test_unknown_format_rejected(self):
        response = self.create_snippet({"format": "markdown", "content": "# Hi"})
        self.assert_problem_response(response, status_code=422)
        self.assertFalse(UUIDSnippetWithRelations.objects.exists())

    def test_write_response_honours_format(self):
        # Write endpoints return the detail schema, so the format applies
        # there too.
        response = self.create_snippet(
            '<p><a linktype="page" id="2">home</a></p>',
            "rich_text_format=html",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("<a href=", response.json()["rich_body"])

    def test_omitted_blank_rich_body_allowed(self):
        # rich_body is blank=True, so omitting it entirely is fine. The
        # Draftail widget round-trip normalises the empty value to an empty
        # paragraph, so what gets stored is not "".
        response = self.post({"text": "Hello"})
        self.assertEqual(response.status_code, 201)
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertRegex(snippet.rich_body, r'^<p data-block-key="[a-z0-9]+"></p>$')


class TestV3SnippetCreateWithRichTextMarkdown(TestV3SnippetCreateBase):
    model = UUIDSnippetWithRelations

    def create_snippet(self, content, rich_text_format="db_markdown"):
        return self.post(
            {
                "text": "Hello",
                "rich_body": {"format": rich_text_format, "content": content},
            }
        )

    def test_db_markdown_input_on_create(self):
        response = self.create_snippet("# Title\n\n[home](wagtail://page?id=2)")
        self.assertEqual(response.status_code, 201, response.json())
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        # h1 is out of the field's features → unwrapped; page reference kept by id
        self.assertNotIn("<h1", snippet.rich_body)
        self.assertIn("Title", snippet.rich_body)
        self.assertIn('linktype="page"', snippet.rich_body)
        self.assertIn('id="2"', snippet.rich_body)

    def test_malformed_reference_gives_422_with_field_and_line(self):
        response = self.create_snippet("[x](wagtail://page?id=abc)")
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

    def test_wagtail_ref_without_id_gives_422(self):
        # A wagtail:// reference missing its id must fail validation, never 500.
        response = self.create_snippet("[x](wagtail://page)")
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

    def test_empty_image_format_stripped_not_stored(self):
        # `format=` (empty) behaves like a missing format: the embed is
        # dropped, never stored verbatim to poison later output.
        response = self.create_snippet("![a](wagtail://image?id=1&format=)")
        self.assertEqual(response.status_code, 201, response.json())
        snippet = UUIDSnippetWithRelations.objects.get(text="Hello")
        self.assertNotIn('format=""', snippet.rich_body)


class TestV3SnippetCreateWithDraftState(TestV3SnippetCreateBase):
    """meta.action support for DraftStateMixin snippets."""

    model = FullFeaturedSnippet

    def test_create_with_publish_action_publishes(self):
        response = self.post(
            {"meta": {"action": "publish"}, "text": "Hello", "some_number": 1}
        )
        self.assertEqual(response.status_code, 201)
        snippet = FullFeaturedSnippet.objects.get(text="Hello")
        self.assertTrue(snippet.live)
        self.assertIsNotNone(snippet.live_revision)

    def test_user_with_add_but_not_publish_permission_with_publish_action(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(
            Permission.objects.get(codename="add_fullfeaturedsnippet")
        )
        self.login(username="adder", password="password")
        response = self.post(
            {"meta": {"action": "publish"}, "text": "Hello", "some_number": 1}
        )
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains=(
                "You do not have permission to publish this full-featured snippet."
            ),
        )

        self.assertFalse(FullFeaturedSnippet.objects.filter(text="Hello").exists())

    def test_create_without_action_does_not_publish(self):
        response = self.post({"text": "Hello", "some_number": 1})
        self.assertEqual(response.status_code, 201)
        snippet = FullFeaturedSnippet.objects.get(text="Hello")
        self.assertFalse(snippet.live)
        self.assertIsNone(snippet.live_revision)

    def test_create_saves_one_revision_and_logs_create(self):
        response = self.post({"text": "Hello", "some_number": 1})
        self.assertEqual(response.status_code, 201)
        snippet = FullFeaturedSnippet.objects.get(text="Hello")
        self.assertEqual(snippet.revisions.count(), 1)
        self.assert_log_actions(snippet, ["wagtail.create"])

    def test_required_field_can_be_blank_when_saved_as_draft(self):
        response = self.post({"text": "", "some_number": 1})
        self.assertEqual(response.status_code, 201)
        snippet = FullFeaturedSnippet.objects.get(some_number=1)
        self.assertFalse(snippet.live)
        self.assertEqual(snippet.text, "")

    def test_missing_required_field_returns_422_on_publish(self):
        response = self.post(
            {"meta": {"action": "publish"}, "text": "", "some_number": 1}
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "required",
                    "loc": ["text"],
                    "msg": "This field is required.",
                }
            ],
        )

    def test_create_with_invalid_action_returns_422(self):
        response = self.post(
            {
                "meta": {"action": "not_a_real_action"},
                "text": "Hello",
                "some_number": 1,
            }
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


class TestV3SnippetCreateWithPermissionedFields(TestV3SnippetCreateBase):
    model = RevisableChildModel

    def test_superuser_can_create_with_secret_text(self):
        response = self.post({"text": "Hello", "secret_text": "s3kr3t"})
        self.assertEqual(response.status_code, 201)
        snippet = RevisableChildModel.objects.get(pk=response.json()["id"])
        self.assertEqual(snippet.text, "Hello")
        self.assertEqual(snippet.secret_text, "s3kr3t")

    def test_user_with_add_permission_cannot_set_secret_text(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(
            Permission.objects.get(codename="add_revisablechildmodel")
        )
        self.login(user)
        response = self.post({"text": "Hello", "secret_text": "should be ignored"})
        self.assertEqual(response.status_code, 201)
        snippet = RevisableChildModel.objects.get(pk=response.json()["id"])
        self.assertEqual(snippet.text, "Hello")
        # secret_text was dropped from the form for this user, so it keeps
        # its default rather than the submitted value
        self.assertEqual(snippet.secret_text, "")
