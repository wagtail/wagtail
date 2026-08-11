import json

from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Page
from wagtail.test.testapp.models import (
    DefaultRichTextFieldPage,
    RichTextFieldWithFeaturesPage,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3RichTextWrite(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.user = self.login()

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_page"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def create_page(self, body, model="tests.DefaultRichTextFieldPage", title="Rich"):
        return self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": model},
                "title": title,
                "slug": "rich",
                "body": body,
            }
        )

    def test_plain_string_stored_sanitised(self):
        response = self.create_page("<p><b>x</b></p><script>alert(1)</script>")
        self.assertEqual(response.status_code, 201)
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        self.assertNotIn("<script", page.body)
        self.assertIn("<b>x</b>", page.body)

    def test_envelope_stored_sanitised(self):
        response = self.create_page(
            {"format": "db_html", "content": "<p>hi <script>alert(1)</script></p>"}
        )
        self.assertEqual(response.status_code, 201)
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        self.assertNotIn("<script", page.body)

    def test_entity_references_survive(self):
        response = self.create_page('<p><a linktype="page" id="2">home</a></p>')
        self.assertEqual(response.status_code, 201)
        page = DefaultRichTextFieldPage.objects.get(slug="rich")
        self.assertIn('linktype="page"', page.body)
        self.assertIn('id="2"', page.body)

    def test_unknown_format_rejected_with_422(self):
        response = self.create_page({"format": "markdown", "content": "# Hi"})
        self.assert_problem_response(response, status_code=422)

    def create_page_without_body(self, action=None):
        meta = {
            "parent_id": self.root_page.pk,
            "type": "tests.DefaultRichTextFieldPage",
        }
        if action:
            meta["action"] = action
        return self.post(
            {
                "meta": meta,
                "title": "No body",
                "slug": "no-body",
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
        page = DefaultRichTextFieldPage.objects.get(slug="no-body")
        self.assertRegex(page.body, r"^<p data-block-key=\"[a-z0-9]+\"></p>$")

    def test_omitted_required_body_allowed_on_publish(self):
        # Publish runs full form validation, but the widget round-trip's
        # empty-paragraph markup is non-empty, so a required body left out of
        # the payload still publishes — admin parity for an untouched
        # Draftail field. (The write schema deliberately adds no schema-level
        # strictness; see the plan's Task 3 ruling.)
        response = self.create_page_without_body(action="publish")
        self.assertEqual(response.status_code, 201)
        page = DefaultRichTextFieldPage.objects.get(slug="no-body")
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
        page = RichTextFieldWithFeaturesPage.objects.get(slug="rich")
        self.assertNotIn("<h2>", page.body)
        self.assertNotIn("<b>", page.body)

    def test_warnings_itemise_stripped_content(self):
        response = self.create_page("<h1>T</h1><p>ok</p>")
        self.assertEqual(response.status_code, 201)
        warnings = response.json()["meta"]["warnings"]
        self.assertEqual(len(warnings), 1)
        warning = warnings[0]
        self.assertEqual(warning["field"], "body")
        self.assertEqual(warning["tag"], "h1")
        self.assertEqual(warning["action"], "unwrapped")
        self.assertEqual(warning["reason"], "feature_disabled")
        self.assertEqual(warning["detail"], "<h1>T</h1>")

    def test_no_warnings_key_when_nothing_stripped(self):
        response = self.create_page("<p>ok</p>")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json()["meta"]["warnings"])

    def test_patch_reports_warnings(self):
        page = DefaultRichTextFieldPage(title="Rich", slug="rich", body="<p>old</p>")
        self.root_page.add_child(instance=page)
        response = self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": page.pk}),
            data=json.dumps({"body": "<h1>T</h1><p>new</p>"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        warnings = response.json()["meta"]["warnings"]
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0]["field"], "body")
