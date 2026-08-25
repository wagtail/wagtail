from django.contrib.admin.utils import quote
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    AdvertWithCustomPrimaryKey,
    FullFeaturedSnippet,
    UUIDSnippetWithRelations,
)
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3SnippetDetailBase(TestV3Base, WagtailTestUtils, TestCase):
    model = Advert

    def get_response(self, pk=None, **params):
        return self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={"type": self.model._meta.label, "pk": pk or self.snippet.pk},
            ),
            params,
        )


class TestV3SnippetDetail(TestV3SnippetDetailBase):
    def setUp(self):
        super().setUp()
        self.advert = Advert.objects.create(text="Advert 1", url="https://wagtail.org")

    def test_anonymous_returns_401(self):
        response = self.get_response(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Unauthorized",
        )

    def test_detail_returns_correct_fields(self):
        self.login()
        response = self.get_response(self.advert.pk)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(set(content.keys()), {"id", "url", "text", "tags", "meta"})
        self.assertEqual(content["id"], self.advert.pk)
        self.assertEqual(content["text"], "Advert 1")
        self.assertEqual(content["url"], "https://wagtail.org")
        self.assertEqual(content["meta"]["type"], "tests.Advert")

    def test_user_without_any_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_unknown_pk_returns_404(self):
        self.login()
        response = self.get_response(999999)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Advert matches the given query.",
        )

    def test_detail_with_quotable_pk(self):
        advert = AdvertWithCustomPrimaryKey.objects.create(
            advert_id=QUOTABLE_PK, text="Advert 1"
        )
        self.login()
        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={
                    "type": "tests.AdvertWithCustomPrimaryKey",
                    "pk": quote(advert.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["advert_id"], QUOTABLE_PK)
        self.assertEqual(content["text"], "Advert 1")

    @override_settings(WAGTAILAPI_BASE_URL="https://api.example.com")
    def test_detail_url_uses_base_url_setting(self):
        self.login()
        response = self.get_response(self.advert.pk)
        content = response.json()
        self.assertTrue(
            content["meta"]["detail_url"].startswith("https://api.example.com")
        )
        self.assertIn(
            f"/api/v3/snippets/tests.Advert/{self.advert.pk}/",
            content["meta"]["detail_url"],
        )


class TestV3SnippetDetailWithRichText(TestV3SnippetDetailBase):
    model = UUIDSnippetWithRelations

    @classmethod
    def setUpTestData(cls):
        cls.home_page = Page.objects.get(depth=2)
        cls.snippet = cls.model.objects.create(
            text="Hello", rich_body=cls.build_rich_body()
        )

    def setUp(self):
        super().setUp()
        self.user = self.login()

    @classmethod
    def build_rich_body(cls):
        return f'<p><a linktype="page" id="{cls.home_page.pk}">home</a></p>'

    def body_value(self, response):
        return response.json()["rich_body"]

    def test_default_output_is_db_html(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.body_value(response), self.build_rich_body())

    def test_html_output_expands_references(self):
        response = self.get_response(rich_text_format="html")
        self.assertEqual(response.status_code, 200)
        body = self.body_value(response)
        self.assertIn("<a href=", body)
        self.assertNotIn("linktype", body)

    def test_invalid_format_is_422_problem_json(self):
        response = self.get_response(rich_text_format="nope")
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

    @override_settings(WAGTAILAPI_RICH_TEXT_FORMAT="html")
    def test_project_wide_default_setting(self):
        response = self.get_response()
        self.assertIn("<a href=", self.body_value(response))

    def test_db_markdown_output_on_detail(self):
        response = self.get_response(rich_text_format="db_markdown")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.body_value(response),
            "[home](wagtail://page?id=%d)\n\n" % self.home_page.pk,
        )

    def test_markdown_output_resolves_reference(self):
        response = self.get_response(rich_text_format="markdown")
        home_url = self.home_page.url or "/"
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.body_value(response), "[home](%s)\n\n" % home_url)

    def test_output_uses_field_features(self):
        # rich_body does not declare h2 in features, so the stored <h2> cannot
        # convert to a contentstate heading and must not appear as `## ` in
        # markdown output. (ORM save stores verbatim.)
        self.snippet.rich_body = "<h2>Title</h2>"
        self.snippet.save()
        response = self.get_response(rich_text_format="db_markdown")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("## ", self.body_value(response))
        self.assertIn("Title", self.body_value(response))


class TestV3SnippetDetailVersion(TestV3Base, WagtailTestUtils, TestCase):
    model = FullFeaturedSnippet

    def get_response(self, pk, **params):
        return self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={"type": self.model._meta.label, "pk": pk},
            ),
            params,
        )

    def test_version_draft_returns_latest_revision_content(self):
        snippet = FullFeaturedSnippet.objects.create(text="Published text")
        user = self.login()
        snippet.text = "Draft text"
        snippet.save_revision(user=user)

        response = self.get_response(snippet.pk, version="draft")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Draft text")

    def test_version_defaults_to_live(self):
        snippet = FullFeaturedSnippet.objects.create(text="Published text")
        user = self.login()
        snippet.text = "Draft text"
        snippet.save_revision(user=user)

        response = self.get_response(snippet.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Published text")

    def test_version_draft_ignored_for_non_draftstate_model(self):
        advert = Advert.objects.create(text="Advert 1", url="https://wagtail.org")
        self.login()

        response = self.client.get(
            reverse(
                "wagtailapi_v3:detail_snippet",
                kwargs={"type": "tests.Advert", "pk": advert.pk},
            ),
            {"version": "draft"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["text"], "Advert 1")

    def test_version_invalid_value_gives_error(self):
        snippet = FullFeaturedSnippet.objects.create(text="Published text")
        self.login()

        response = self.get_response(snippet.pk, version="published")
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "literal_error",
                    "loc": ["query", "version"],
                    "msg": "Input should be 'live' or 'draft'",
                }
            ],
        )
