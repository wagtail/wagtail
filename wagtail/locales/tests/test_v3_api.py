import json

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Locale
from wagtail.test.utils import Page, WagtailTestUtils

LOCALE_FIELDS = {
    "meta",
    "id",
    "language_code",
    "display_name",
    "is_bidi",
    "is_default",
}


class TestV3LocaleListing(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        Locale.objects.create(language_code="fr")

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_locales"), params)

    def test_anonymous_returns_401(self):
        response = self.get_response()
        self.assert_problem_response(response, status_code=401)

    def test_authenticated_returns_200(self):
        self.login()
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_response_fields(self):
        self.login()
        content = self.get_response().json()
        self.assertIn("count", content)
        self.assertIn("items", content)
        for item in content["items"]:
            self.assertEqual(set(item.keys()), LOCALE_FIELDS)

    def test_count_matches_database(self):
        self.login()
        content = self.get_response().json()
        self.assertEqual(content["count"], Locale.objects.count())

    def test_user_with_any_locale_permission_can_list(self):
        user = self.create_user(username="viewer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="view_locale"))
        self.login(username="viewer", password="password")
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_user_without_any_locale_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response()
        self.assert_problem_response(response, status_code=403)


class TestV3LocaleDetail(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.locale = Locale.objects.create(language_code="fr")

    def get_response(self, locale_id):
        return self.client.get(
            reverse("wagtailapi_v3:detail_locale", kwargs={"locale_id": locale_id})
        )

    def test_anonymous_returns_401(self):
        response = self.get_response(self.locale.pk)
        self.assert_problem_response(response, status_code=401)

    def test_detail_returns_correct_fields(self):
        self.login()
        response = self.get_response(self.locale.pk)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(set(content.keys()), LOCALE_FIELDS)
        self.assertEqual(content["meta"]["type"], "wagtailcore.Locale")
        self.assertEqual(content["id"], self.locale.pk)
        self.assertEqual(content["language_code"], "fr")
        self.assertEqual(content["display_name"], "French")
        self.assertEqual(content["is_bidi"], False)
        self.assertEqual(content["is_default"], False)

    def test_user_without_any_locale_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response(self.locale.pk)
        self.assert_problem_response(response, status_code=403)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.get_response(999999)
        self.assert_problem_response(response, status_code=404)


class TestV3LocaleCreate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.valid_payload = {"language_code": "fr"}

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_locale"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create(self):
        self.login()
        initial_count = Locale.objects.count()
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Locale.objects.count(), initial_count + 1)
        content = response.json()
        self.assertEqual(set(content.keys()), LOCALE_FIELDS)
        self.assertEqual(content["language_code"], "fr")

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_add_permission_can_create(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(Permission.objects.get(codename="add_locale"))
        self.login(user)
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_language_code_returns_422(self):
        self.login()
        Locale.objects.create(language_code="fr")
        response = self.post(self.valid_payload)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "invalid_choice",
                    "loc": ["language_code"],
                    "msg": "Select a valid choice. "
                    "fr is not one of the available choices.",
                }
            ],
        )

    def test_unsupported_language_code_returns_422(self):
        self.login()
        response = self.post({"language_code": "xx"})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "invalid_choice",
                    "loc": ["language_code"],
                    "msg": "Select a valid choice. "
                    "xx is not one of the available choices.",
                }
            ],
        )


class TestV3LocaleUpdate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.locale = Locale.objects.create(language_code="fr")
        self.valid_payload = {"language_code": "fr"}

    def put(self, locale_id, data):
        return self.client.put(
            reverse("wagtailapi_v3:update_locale", kwargs={"locale_id": locale_id}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.put(self.locale.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update(self):
        self.login()
        # "en" is already used by the default locale, so it is not offered as
        # a choice for "fr" to change into; keep the same code but confirm
        # the endpoint round-trips successfully.
        response = self.put(self.locale.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)
        self.locale.refresh_from_db()
        self.assertEqual(self.locale.language_code, "fr")

    def test_user_without_change_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.put(self.locale.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_change_permission_can_update(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="change_locale"))
        self.login(username="changer", password="password")
        response = self.put(self.locale.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.put(999999, self.valid_payload)
        self.assert_problem_response(response, status_code=404)

    def test_response_fields(self):
        self.login()
        response = self.put(self.locale.pk, self.valid_payload)
        content = response.json()
        self.assertEqual(set(content.keys()), LOCALE_FIELDS)

    def test_duplicate_language_code_returns_422(self):
        self.login()
        other = Locale.objects.get(language_code="en")
        response = self.put(self.locale.pk, {"language_code": other.language_code})
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "type": "invalid_choice",
                    "loc": ["language_code"],
                    "msg": "Select a valid choice. "
                    "en is not one of the available choices.",
                }
            ],
        )


class TestV3LocaleDelete(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.locale = Locale.objects.create(language_code="fr")

    def delete(self, locale_id):
        return self.client.delete(
            reverse("wagtailapi_v3:delete_locale", kwargs={"locale_id": locale_id})
        )

    def test_anonymous_returns_401(self):
        response = self.delete(self.locale.pk)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_delete(self):
        self.login()
        pk = self.locale.pk
        response = self.delete(pk)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Locale.objects.filter(pk=pk).exists())

    def test_user_without_delete_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.delete(self.locale.pk)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_delete_permission_can_delete(self):
        user = self.create_user(username="deleter", password="password")
        user.user_permissions.add(Permission.objects.get(codename="delete_locale"))
        self.login(user)
        response = self.delete(self.locale.pk)
        self.assertEqual(response.status_code, 204)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.delete(999999)
        self.assert_problem_response(response, status_code=404)

    def test_cannot_delete_last_locale(self):
        self.login()
        Page.objects.filter(depth__gt=1).delete()
        for other in Locale.objects.exclude(pk=self.locale.pk):
            other.delete()
        response = self.delete(self.locale.pk)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "msg": "This locale cannot be deleted because "
                    "there are no other locales."
                }
            ],
        )
        self.assertTrue(Locale.objects.filter(pk=self.locale.pk).exists())

    def test_cannot_delete_locale_in_use(self):
        self.login()
        root_page = Page.objects.get(depth=1)
        root_page.add_child(
            instance=Page(title="French page", locale=self.locale, slug="french-page")
        )
        response = self.delete(self.locale.pk)
        self.assert_problem_response(
            response,
            status_code=422,
            detail_contains="Validation failed",
            errors=[
                {
                    "msg": "This locale cannot be deleted because "
                    "there are pages and/or other objects using it."
                }
            ],
        )
        self.assertTrue(Locale.objects.filter(pk=self.locale.pk).exists())
