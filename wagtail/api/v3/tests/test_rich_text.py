import json

from django.core.serializers.json import DjangoJSONEncoder
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.api import api
from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import (
    CustomRichBlockFieldPage,
    DefaultRichBlockFieldPage,
    DefaultRichTextFieldPage,
    RichTextFieldWithFeaturesPage,
)
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3RichTextWrite(TestV3Base, WagtailTestUtils, TestCase):
    model = DefaultRichTextFieldPage

    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.user = self.login()
        self.type_name = self.model._meta.label

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_page"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def build_body(self, value):
        return value

    def body_value(self, page):
        return page.body

    def create_page(self, value, model=None, title="Rich"):
        return self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": model or self.type_name,
                },
                "title": title,
                "slug": "rich",
                "body": self.build_body(value),
            }
        )

    def test_plain_string_stored_sanitised(self):
        response = self.create_page("<p><b>x</b></p><script>alert(1)</script>")
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="rich")
        value = self.body_value(page)
        self.assertNotIn("<script", value)
        self.assertIn("<b>x</b>", value)

    def test_envelope_stored_sanitised(self):
        response = self.create_page(
            {"format": "db_html", "content": "<p>hi <script>alert(1)</script></p>"}
        )
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="rich")
        value = self.body_value(page)
        self.assertNotIn("<script", value)
        self.assertRegex(value, r"^<p data-block-key=\"[a-z0-9]+\">hi alert\(1\)</p>$")

    def test_entity_references_survive(self):
        response = self.create_page('<p><a linktype="page" id="2">home</a></p>')
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="rich")
        value = self.body_value(page)
        self.assertIn('linktype="page"', value)
        self.assertIn('id="2"', value)

    def test_unknown_format_rejected(self):
        response = self.create_page({"format": "markdown", "content": "# Hi"})
        self.assert_problem_response(response, status_code=422)

    def create_page_without_body(self, action=None, **data):
        meta = {
            "parent_id": self.root_page.pk,
            "type": self.type_name,
        }
        if action:
            meta["action"] = action
        return self.post(
            {
                "meta": meta,
                "title": "No body",
                "slug": "no-body",
                **data,
            }
        )

    def test_omitted_required_body_allowed_for_draft(self):
        # DefaultRichTextFieldPage.body is a required RichTextField. The write
        # schema keeps rich text fields optional (schema default ""), and a
        # draft create defers required-field validation — same as the admin.
        # Draftail's widget round-trip normalises the empty value to an empty
        # paragraph, so what gets stored is not "".
        response = self.create_page_without_body()
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="no-body")
        self.assertRegex(
            self.body_value(page),
            r"^<p data-block-key=\"[a-z0-9]+\"></p>$",
        )

    def test_omitted_required_body_allowed_on_publish(self):
        # Publish runs full form validation, but the widget round-trip's
        # empty-paragraph markup is non-empty, so a required body left out of
        # the payload still publishes — admin parity for an untouched
        # Draftail field. (The write schema deliberately adds no schema-level
        # strictness; see the plan's Task 3 ruling.)
        response = self.create_page_without_body(action="publish")
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="no-body")
        self.assertTrue(page.live)

    def test_feature_restricted_field_strips_out_of_features(self):
        # RichTextFieldWithFeaturesPage body: features=["quotation", "embed",
        # "made-up-feature"] — bold/h2 are not enabled.
        response = self.create_page(
            "<h2>T</h2><p><b>x</b></p>",
            model="tests.RichTextFieldWithFeaturesPage",
            title="Restricted",
        )
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
        page = RichTextFieldWithFeaturesPage.objects.get(slug="rich")
        self.assertNotIn("<h2>", page.body)
        self.assertNotIn("<b>", page.body)

    def test_with_db_markdown(self):
        response = self.create_page(
            {
                "format": "db_markdown",
                "content": "# Title\n\n[home](wagtail://page?id=2)",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = self.model.objects.get(slug="rich")
        body = self.body_value(page)
        self.assertNotIn("<h1", body)
        self.assertIn("Title", body)
        self.assertIn('linktype="page"', body)
        self.assertIn('id="2"', body)

    def test_with_incorrect_db_markdown(self, loc=None):
        response = self.create_page(
            {
                "format": "db_markdown",
                "content": "[home](wagtail://page?)",
            }
        )
        data = self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
        )
        loc = loc or ["body", "data", self.model._meta.label, "body"]
        self.assertEqual(len(data["errors"]), 1)
        self.assertEqual(data["errors"][0]["loc"], loc)
        self.assertIn(
            "Invalid Markdown in rich text: wagtail://page reference requires id",
            data["errors"][0]["msg"],
        )
        self.assertFalse(self.model.objects.filter(slug="rich").exists())


class TestV3RichTextBlockWrite(TestV3RichTextWrite):
    """RichTextBlock counterpart of TestV3RichTextWrite."""

    model = DefaultRichBlockFieldPage
    type_name = "tests.DefaultRichBlockFieldPage"

    def build_body(self, value):
        return [{"type": "rich_text", "value": value}]

    def body_value(self, page):
        return page.body[0].value.source

    def create_page_without_body(self, action=None, **data):
        # Rather than an empty StreamField body, add a single rich_text block
        # with an empty value for testing empty input.
        return super().create_page_without_body(
            action,
            body=[{"type": "rich_text", "value": ""}],
        )

    def create_page_with_block(self, block_type, value, model, title):
        return self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": model},
                "title": title,
                "slug": "rich",
                "body": [{"type": block_type, "value": value}],
            }
        )

    def test_feature_restricted_field_strips_out_of_features(self):
        # CustomRichBlockFieldPage.rich_text_limited block: features=
        # ["quotation", "embed"] - bold/h2 are not enabled.
        response = self.create_page_with_block(
            "rich_text_limited",
            "<h2>T</h2><p><b>x</b></p>",
            model="tests.CustomRichBlockFieldPage",
            title="Restricted",
        )
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
        page = CustomRichBlockFieldPage.objects.get(slug="rich")
        value = page.body[0].value.source
        self.assertNotIn("<h2>", value)
        self.assertNotIn("<b>", value)

    def test_unrestricted_block_on_same_page_keeps_its_own_features(self):
        # The plain "rich_text" block on CustomRichBlockFieldPage has no
        # features restriction, unlike its sibling "rich_text_limited" block.
        response = self.create_page_with_block(
            "rich_text",
            "<h2>T</h2><p><b>x</b></p>",
            model="tests.CustomRichBlockFieldPage",
            title="Unrestricted",
        )
        self.assertEqual(response.status_code, 201)
        page = CustomRichBlockFieldPage.objects.get(slug="rich")
        value = page.body[0].value.source
        self.assertIn("<h2>", value)
        self.assertIn("<b>", value)

    def test_with_incorrect_db_markdown(self, loc=None):
        return super().test_with_incorrect_db_markdown(loc=["body-0-value"])


class TestV3RichTextRead(TestV3Base, WagtailTestUtils, TestCase):
    model = DefaultRichTextFieldPage
    type_name = "tests.DefaultRichTextFieldPage"

    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.user = self.login()
        self.home_page = Page.objects.get(depth=2)
        self.page = self.model(
            title="Rich",
            slug="rich",
            body=self.build_body(
                f'<p><a linktype="page" id="{self.home_page.pk}">home</a></p>'
            ),
        )
        # The detail endpoint serves the public queryset: live pages under
        # the default site's root (the depth-2 home page).
        self.home_page.add_child(instance=self.page)
        self.page.save_revision().publish()

    def build_body(self, html):
        """The api_fields "body" payload/model value for a given rich text
        HTML string - a plain string for RichTextField."""
        return html

    def body_value(self, response):
        """Extract the rich text HTML from a response's "body" value."""
        return response.json()["body"]

    def get_detail(self, **params):
        return self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": self.page.pk}),
            data=params,
        )

    def test_default_output_is_db_html(self):
        response = self.get_detail()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.body_value(response),
            f'<p><a linktype="page" id="{self.home_page.pk}">home</a></p>',
        )

    def test_html_output_expands_references(self):
        response = self.get_detail(rich_text_format="html")
        self.assertEqual(response.status_code, 200)
        body = self.body_value(response)
        self.assertIn("<a href=", body)
        self.assertNotIn("linktype", body)

    def test_invalid_format_is_422_problem_json(self):
        response = self.get_detail(rich_text_format="nope")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "literal_error",
                    "loc": ["query", "rich_text_format"],
                    "msg": "Input should be 'db_html', 'html', 'db_markdown' or 'markdown'",
                }
            ],
        )

    def test_write_response_honours_format(self):
        # Write endpoints return the detail schema, so the format applies
        # there too. (The list endpoint serialises BasePageSchema only — no
        # api_fields extras like body — so it takes no rich_text_format param.)
        response = self.client.post(
            reverse("wagtailapi_v3:create_page") + "?rich_text_format=html",
            data=json.dumps(
                {
                    "meta": {
                        "parent_id": self.root_page.pk,
                        "type": self.type_name,
                    },
                    "title": "Rich html",
                    "slug": "rich-html",
                    "body": self.build_body(
                        f'<p><a linktype="page" id="{self.home_page.pk}">home</a></p>'
                    ),
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("<a href=", self.body_value(response))

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="html")
    def test_project_wide_default_setting(self):
        response = self.get_detail()
        self.assertIn("<a href=", self.body_value(response))

    def test_features_in_schema_discovery(self):
        response = self.client.get(
            reverse(
                "wagtailapi_v3:get_schema_for_type",
                kwargs={"type_name": self.type_name},
            )
        )
        self.assertEqual(response.status_code, 200)
        read_schema = response.json()["read"]
        body_schema = read_schema["properties"]["body"]
        self.assertIn("x-rich-text-features", body_schema)
        self.assertIn("bold", body_schema["x-rich-text-features"])


class TestV3RichTextBlockRead(TestV3RichTextRead):
    """RichTextBlock counterpart of TestV3RichTextRead."""

    model = DefaultRichBlockFieldPage
    type_name = "tests.DefaultRichBlockFieldPage"

    def build_body(self, html):
        return [{"type": "rich_text", "value": html}]

    def body_value(self, response):
        [block] = response.json()["body"]
        return block["value"]

    def test_features_in_schema_discovery(self):
        self.skipTest("StreamField body has no per-block schema to carry features")


class TestV3RichTextMarkdown(TestV3RichTextWrite):
    """db_markdown input (create/patch) + db_markdown/markdown output on
    reads, wired through the v3 pages endpoints."""

    def publish_detail_page(self, **kwargs):
        """Add a live rich-text page the public detail endpoint can serve."""
        model = kwargs.pop("model", DefaultRichTextFieldPage)
        home_page = Page.objects.get(depth=2)
        page = model(slug="md-detail", title="MD detail", **kwargs)
        home_page.add_child(instance=page)
        page.save_revision().publish()
        return page

    def test_db_markdown_input_on_create(self):
        response = self.create_page(
            {
                "format": "db_markdown",
                "content": "# Title\n\n[home](wagtail://page?id=2)",
            }
        )
        self.assertEqual(response.status_code, 201, response.json())
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        # h1 is out of the default features → unwrapped; page reference kept by id
        self.assertNotIn("<h1", page.body)
        self.assertIn("Title", page.body)
        self.assertIn('linktype="page"', page.body)
        self.assertIn('id="2"', page.body)

    def test_db_markdown_input_on_patch(self):
        self.create_page({"format": "db_markdown", "content": "**before**"})
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        response = self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": page.pk}),
            data=json.dumps(
                {
                    "meta": {"type": "tests.DefaultRichTextFieldPage"},
                    "body": {"format": "db_markdown", "content": "**after**"},
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.json())
        page.refresh_from_db()
        self.assertIn("<b>after</b>", page.body)
        self.assertNotIn("<b>before</b>", page.body)

    def test_malformed_reference_gives_422_with_field_and_line(self):
        response = self.create_page(
            {"format": "db_markdown", "content": "[x](wagtail://page?id=abc)"}
        )
        self.assert_problem_response(response, status_code=422)
        body = json.dumps(response.json())
        self.assertIn("body", body)
        self.assertIn("abc", body)

    def test_wagtail_ref_without_id_gives_422(self):
        # A wagtail:// reference missing its id must fail validation, never 500.
        response = self.create_page(
            {"format": "db_markdown", "content": "[x](wagtail://page)"}
        )
        self.assert_problem_response(response, status_code=422)
        body = json.dumps(response.json())
        self.assertIn("body", body)
        self.assertIn("requires id", body)

    def test_empty_image_format_stripped_not_stored(self):
        # `format=` (empty) behaves like a missing format: the embed is
        # dropped, never stored verbatim to poison later output.
        response = self.create_page(
            {"format": "db_markdown", "content": "![a](wagtail://image?id=1&format=)"}
        )
        self.assertEqual(response.status_code, 201, response.json())
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        self.assertNotIn('format=""', page.body)

    def test_markdown_format_still_rejected_as_input(self):
        response = self.create_page({"format": "markdown", "content": "# hi"})
        self.assert_problem_response(response, status_code=422)

    def test_db_markdown_output_on_detail(self):
        page = self.publish_detail_page(
            body='<p><a linktype="page" id="2">home</a></p>'
        )
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
            + "?rich_text_format=db_markdown"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["body"], "[home](wagtail://page?id=2)\n\n")

    def test_markdown_output_resolves_reference(self):
        page = self.publish_detail_page(
            body='<p><a linktype="page" id="2">home</a></p>'
        )
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
            + "?rich_text_format=markdown"
        )
        home_url = Page.objects.get(depth=2).url or "/"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["body"], "[home](%s)\n\n" % home_url)

    def test_output_uses_field_features(self):
        # RichTextFieldWithFeaturesPage declares features ["quotation",
        # "embed", "made-up-feature"]: h2 is not among them, so the field's
        # stored <h2> cannot convert to a contentstate heading and must not
        # appear as `## ` in markdown output. (ORM save stores verbatim.)
        page = self.publish_detail_page(
            model=RichTextFieldWithFeaturesPage, body="<h2>Title</h2>"
        )
        response = self.client.get(
            reverse("wagtailapi_v3:detail_page", kwargs={"page_id": page.pk})
            + "?rich_text_format=db_markdown"
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("## ", response.json()["body"])
        self.assertIn("Title", response.json()["body"])

    def test_openapi_lists_new_formats(self):
        # DjangoJSONEncoder handles the lazy translation strings in descriptions.
        spec = json.dumps(api.get_openapi_schema(), cls=DjangoJSONEncoder)
        self.assertIn('"db_markdown"', spec)
        self.assertIn('"markdown"', spec)
