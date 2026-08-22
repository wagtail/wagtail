import json

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    AdvertWithCustomPrimaryKey,
    FullFeaturedSnippet,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetActionsBase(TestV3Base, WagtailTestUtils, TestCase):
    model = FullFeaturedSnippet

    def login_with_permissions(self, *codenames, index=0):
        """
        Log in as a fresh non-superuser with exactly the given permission
        codenames on ``self.model``. Passing no codenames logs in a user with
        no permissions on the model at all. ``index`` keeps usernames unique
        within a single test method (e.g. across a permission_matrix loop).
        """
        username = f"user-{index}"
        user = self.create_user(username=username, password="password")
        for codename in codenames:
            user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label=self.model._meta.app_label,
                    codename=codename,
                )
            )
        self.login(username=username, password="password")
        return user


class TestV3SnippetPublish(TestV3SnippetActionsBase):
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_fullfeaturedsnippet"], 403),
        (["publish_fullfeaturedsnippet"], 200),
    ]

    def post(self, snippet):
        return self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_publish",
                kwargs={"type": self.model._meta.label, "pk": snippet.pk},
            )
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                snippet = FullFeaturedSnippet.objects.create(
                    text=f"Draft {i}", live=False
                )
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.post(snippet)

                self.assertEqual(response.status_code, expected_status)
                snippet.refresh_from_db()
                if expected_status == 200:
                    self.assertTrue(snippet.live)
                    self.assert_log_actions(snippet, ["wagtail.publish"])
                else:
                    self.assertFalse(snippet.live)

    def test_publish_with_no_revision_creates_one(self):
        snippet = FullFeaturedSnippet.objects.create(text="Draft", live=False)
        self.login_with_permissions("publish_fullfeaturedsnippet")
        self.assertIsNone(snippet.get_latest_revision())
        response = self.post(snippet)
        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertTrue(snippet.live)
        self.assertIsNotNone(snippet.get_latest_revision())

    def test_unknown_snippet_returns_404(self):
        self.login_with_permissions("publish_fullfeaturedsnippet")
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_publish",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_non_draftstate_type_is_rejected(self):
        self.login()
        advert = Advert.objects.create(text="Hi")
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_publish",
                kwargs={"type": "tests.Advert", "pk": advert.pk},
            )
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )


class TestV3SnippetUnpublish(TestV3SnippetActionsBase):
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["add_fullfeaturedsnippet"], 403),
        (["publish_fullfeaturedsnippet"], 200),
    ]

    def post(self, snippet):
        return self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_unpublish",
                kwargs={"type": self.model._meta.label, "pk": snippet.pk},
            )
        )

    def make_live_snippet(self, **kwargs):
        snippet = FullFeaturedSnippet.objects.create(live=False, **kwargs)
        snippet.save_revision().publish()
        snippet.refresh_from_db()
        return snippet

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                snippet = self.make_live_snippet(text=f"Live {i}")
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                since = timezone.now()
                response = self.post(snippet)

                self.assertEqual(response.status_code, expected_status)
                snippet.refresh_from_db()
                if expected_status == 200:
                    self.assertFalse(snippet.live)
                    self.assert_log_actions(snippet, ["wagtail.unpublish"], since=since)
                else:
                    self.assertTrue(snippet.live)

    def test_unknown_snippet_returns_404(self):
        self.login_with_permissions("publish_fullfeaturedsnippet")
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_unpublish",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            )
        )
        self.assert_problem_response(response, status_code=404)


class TestV3SnippetDeleteAction(TestV3SnippetActionsBase):
    model = Advert
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["delete_advert"], 204),
    ]

    def delete(self, snippet):
        return self.client.delete(
            reverse(
                "wagtailapi_v3:snippets_actions_delete",
                kwargs={"type": self.model._meta.label, "pk": snippet.pk},
            )
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                advert = Advert.objects.create(text=f"Deletable {i}")
                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.delete(advert)

                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(
                    Advert.objects.filter(pk=advert.pk).exists(),
                    expected_status != 204,
                )

    def test_unknown_snippet_returns_404(self):
        self.login_with_permissions("delete_advert")
        response = self.client.delete(
            reverse(
                "wagtailapi_v3:snippets_actions_delete",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            )
        )
        self.assert_problem_response(response, status_code=404)

    def test_delete_with_quotable_pk(self):
        advert = AdvertWithCustomPrimaryKey.objects.create(
            advert_id=QUOTABLE_PK, text="Deletable"
        )
        self.login_with_permissions("delete_advertwithcustomprimarykey")
        response = self.client.delete(
            reverse(
                "wagtailapi_v3:snippets_actions_delete",
                kwargs={
                    "type": "tests.AdvertWithCustomPrimaryKey",
                    "pk": quote(advert.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            AdvertWithCustomPrimaryKey.objects.filter(pk=QUOTABLE_PK).exists()
        )


class TestV3SnippetRevert(TestV3SnippetActionsBase):
    # Reverting only requires "change" (or "add" on a snippet you own - not
    # applicable to snippets, which have no owner field, so just "change").
    permission_matrix = [
        (None, 401),
        ([], 403),
        (["change_fullfeaturedsnippet"], 200),
    ]

    def post(self, snippet, revision_id):
        return self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_revert",
                kwargs={"type": self.model._meta.label, "pk": snippet.pk},
            ),
            data=json.dumps({"revision_id": revision_id}),
            content_type="application/json",
        )

    def test_permission_matrix(self):
        for i, (codenames, expected_status) in enumerate(self.permission_matrix):
            with self.subTest(codenames=codenames):
                snippet = FullFeaturedSnippet.objects.create(
                    text="Original", live=False
                )
                original_revision = snippet.save_revision()
                snippet.text = "Changed"
                snippet.save_revision()
                snippet.save()

                if codenames is None:
                    self.unauthorize()
                else:
                    self.login_with_permissions(*codenames, index=i)

                response = self.post(snippet, original_revision.pk)

                self.assertEqual(response.status_code, expected_status)
                if expected_status == 200:
                    content = response.json()
                    self.assertEqual(content["text"], "Original")

    def test_revert_creates_new_revision_without_publishing(self):
        self.login()
        snippet = FullFeaturedSnippet.objects.create(text="Original", live=False)
        original_revision = snippet.save_revision()
        snippet.text = "Changed"
        snippet.save_revision()
        snippet.save()

        response = self.post(snippet, original_revision.pk)

        self.assertEqual(response.status_code, 200)
        snippet.refresh_from_db()
        self.assertEqual(snippet.text, "Changed")
        self.assertEqual(snippet.get_latest_revision().as_object().text, "Original")
        self.assert_log_actions(snippet, ["wagtail.revert"])

    def test_unknown_snippet_returns_404(self):
        self.login()
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_revert",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            ),
            data=json.dumps({"revision_id": 1}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_unknown_revision_returns_404(self):
        self.login()
        snippet = FullFeaturedSnippet.objects.create(text="Original", live=False)
        response = self.post(snippet, 999999)
        self.assert_problem_response(response, status_code=404)

    def test_revision_belonging_to_another_snippet_returns_404(self):
        self.login()
        snippet = FullFeaturedSnippet.objects.create(text="Snippet", live=False)
        other_snippet = FullFeaturedSnippet.objects.create(text="Other", live=False)
        other_revision = other_snippet.save_revision()
        response = self.post(snippet, other_revision.pk)
        self.assert_problem_response(response, status_code=404)

    def test_non_revisable_type_is_rejected(self):
        self.login()
        advert = Advert.objects.create(text="Hi")
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_revert",
                kwargs={"type": "tests.Advert", "pk": advert.pk},
            ),
            data=json.dumps({"revision_id": 1}),
            content_type="application/json",
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestV3SnippetCopyForTranslation(TestV3SnippetActionsBase):
    def setUp(self):
        super().setUp()
        self.french = Locale.objects.create(language_code="fr")

    def grant_submit_translation(self, user):
        user.user_permissions.add(Permission.objects.get(codename="submit_translation"))

    def post(self, snippet, data):
        return self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_copy_for_translation",
                kwargs={"type": self.model._meta.label, "pk": snippet.pk},
            ),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_requires_submit_translation_permission(self):
        self.login_with_permissions(
            "add_fullfeaturedsnippet", "change_fullfeaturedsnippet"
        )
        snippet = FullFeaturedSnippet.objects.create(text="Src")
        response = self.post(snippet, {"locale": "fr"})
        self.assert_problem_response(response, status_code=403)

    def test_requires_change_permission_on_source_snippet(self):
        user = self.login_with_permissions("add_fullfeaturedsnippet")
        self.grant_submit_translation(user)
        snippet = FullFeaturedSnippet.objects.create(text="Src")
        response = self.post(snippet, {"locale": "fr"})
        self.assert_problem_response(response, status_code=403)

    def test_copy_for_translation(self):
        user = self.login_with_permissions(
            "add_fullfeaturedsnippet", "change_fullfeaturedsnippet"
        )
        self.grant_submit_translation(user)
        snippet = FullFeaturedSnippet.objects.create(text="Src")

        response = self.post(snippet, {"locale": "fr"})

        self.assertEqual(response.status_code, 201)
        new_snippet = FullFeaturedSnippet.objects.get(pk=response.json()["id"])
        self.assertEqual(new_snippet.locale, self.french)
        self.assertEqual(new_snippet.text, "Src")

    def test_unknown_locale_returns_404(self):
        user = self.login_with_permissions("add_fullfeaturedsnippet")
        self.grant_submit_translation(user)
        snippet = FullFeaturedSnippet.objects.create(text="Src")
        response = self.post(snippet, {"locale": "de"})
        self.assert_problem_response(response, status_code=404)

    def test_unknown_snippet_returns_404(self):
        user = self.login_with_permissions("add_fullfeaturedsnippet")
        self.grant_submit_translation(user)
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_copy_for_translation",
                kwargs={"type": self.model._meta.label, "pk": 999999},
            ),
            data=json.dumps({"locale": "fr"}),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_non_translatable_type_is_rejected(self):
        self.login()
        advert = Advert.objects.create(text="Hi")
        response = self.client.post(
            reverse(
                "wagtailapi_v3:snippets_actions_copy_for_translation",
                kwargs={"type": "tests.Advert", "pk": advert.pk},
            ),
            data=json.dumps({"locale": "fr"}),
            content_type="application/json",
        )
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[{"type": "literal_error", "loc": ["path", "type"]}],
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_disabled_when_i18n_disabled(self):
        user = self.login_with_permissions("add_fullfeaturedsnippet")
        self.grant_submit_translation(user)
        snippet = FullFeaturedSnippet.objects.create(text="Src")
        response = self.post(snippet, {"locale": "fr"})
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="Internationalization is not enabled.",
        )
