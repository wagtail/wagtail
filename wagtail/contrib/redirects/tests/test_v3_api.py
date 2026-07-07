import json

import swapper
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Site
from wagtail.test.utils import WagtailTestUtils

if swapper.is_swapped("wagtailcore", "Page"):
    from wagtail.test.basepage.models import BasePage as Page
else:
    from wagtail.models import Page


REDIRECT_FIELDS = {
    "id",
    "old_path",
    "site_id",
    "is_permanent",
    "redirect_page_id",
    "redirect_page_route_path",
    "redirect_link",
    "automatically_created",
    "created_at",
}


def make_redirect(**kwargs):
    defaults = {
        "old_path": "/test",
        "redirect_link": "https://example.com/",
    }
    defaults.update(kwargs)
    return Redirect.objects.create(**defaults)


class TestV3RedirectListing(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        make_redirect(old_path="/one", redirect_link="https://example.com/one/")
        make_redirect(old_path="/two", redirect_link="https://example.com/two/")

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_redirects"), params)

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
            self.assertEqual(set(item.keys()), REDIRECT_FIELDS)

    def test_count_matches_database(self):
        self.login()
        content = self.get_response().json()
        self.assertEqual(content["count"], Redirect.objects.count())

    def test_default_limit_is_20(self):
        self.login()
        content = self.get_response().json()
        self.assertLessEqual(len(content["items"]), 20)

    def test_user_with_any_redirect_permission_can_list(self):
        user = self.create_user(username="viewer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="view_redirect"))
        self.login(username="viewer", password="password")
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_user_without_any_redirect_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response()
        self.assert_problem_response(response, status_code=403)


class TestV3RedirectDetail(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.redirect = make_redirect(
            old_path="/old", redirect_link="https://example.com/"
        )

    def get_response(self, redirect_id):
        return self.client.get(
            reverse(
                "wagtailapi_v3:detail_redirect", kwargs={"redirect_id": redirect_id}
            )
        )

    def test_anonymous_returns_401(self):
        response = self.get_response(self.redirect.pk)
        self.assert_problem_response(response, status_code=401)

    def test_detail_returns_correct_fields(self):
        self.login()
        response = self.get_response(self.redirect.pk)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(set(content.keys()), REDIRECT_FIELDS)
        self.assertEqual(content["id"], self.redirect.pk)
        self.assertEqual(content["old_path"], "/old")
        self.assertEqual(content["redirect_link"], "https://example.com/")
        self.assertIsNone(content["site_id"])
        self.assertTrue(content["is_permanent"])

    def test_user_without_any_redirect_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response(self.redirect.pk)
        self.assert_problem_response(response, status_code=403)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.get_response(999999)
        self.assert_problem_response(response, status_code=404)


class TestV3RedirectCreate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.valid_payload = {
            "old_path": "/new-old-path",
            "redirect_link": "https://example.com/target/",
            "is_permanent": True,
        }

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_redirect"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create(self):
        self.login()
        initial_count = Redirect.objects.count()
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Redirect.objects.count(), initial_count + 1)
        content = response.json()
        self.assertEqual(set(content.keys()), REDIRECT_FIELDS)
        self.assertEqual(content["old_path"], "/new-old-path")
        self.assertEqual(content["redirect_link"], "https://example.com/target/")

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_add_permission_can_create(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(Permission.objects.get(codename="add_redirect"))
        self.login(user)
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)

    def test_old_path_is_normalised(self):
        self.login()
        payload = dict(self.valid_payload)
        payload["old_path"] = "  /foo/bar/  "
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        content = response.json()
        self.assertEqual(content["old_path"], "/foo/bar")

    def test_duplicate_old_path_and_site_returns_422(self):
        self.login()
        make_redirect(old_path="/new-old-path")
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=422)

    def test_create_with_page_redirect(self):
        self.login()
        page = Page.objects.filter(depth__gt=1).first()
        payload = {"old_path": "/to-page", "redirect_page_id": page.pk}
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        content = response.json()
        self.assertEqual(content["redirect_page_id"], page.pk)

    def test_create_with_site(self):
        self.login()
        site = Site.objects.first()
        payload = dict(self.valid_payload)
        payload["old_path"] = "/site-specific"
        payload["site"] = site.pk
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        content = response.json()
        self.assertEqual(content["site_id"], site.pk)


class TestV3RedirectUpdate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.redirect = make_redirect(
            old_path="/original", redirect_link="https://example.com/"
        )
        self.valid_payload = {
            "old_path": "/updated",
            "redirect_link": "https://example.com/updated/",
            "is_permanent": False,
        }

    def put(self, redirect_id, data):
        return self.client.put(
            reverse(
                "wagtailapi_v3:update_redirect", kwargs={"redirect_id": redirect_id}
            ),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.put(self.redirect.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update(self):
        self.login()
        response = self.put(self.redirect.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)
        self.redirect.refresh_from_db()
        self.assertEqual(self.redirect.old_path, "/updated")
        self.assertFalse(self.redirect.is_permanent)

    def test_user_without_change_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.put(self.redirect.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_change_permission_can_update(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="change_redirect"))
        self.login(username="changer", password="password")
        response = self.put(self.redirect.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.put(999999, self.valid_payload)
        self.assert_problem_response(response, status_code=404)

    def test_response_fields(self):
        self.login()
        response = self.put(self.redirect.pk, self.valid_payload)
        content = response.json()
        self.assertEqual(set(content.keys()), REDIRECT_FIELDS)

    def test_old_path_is_normalised_on_update(self):
        self.login()
        payload = dict(self.valid_payload)
        payload["old_path"] = "  /needs/normalising/  "
        response = self.put(self.redirect.pk, payload)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(content["old_path"], "/needs/normalising")


class TestV3RedirectDelete(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.redirect = make_redirect(
            old_path="/to-delete", redirect_link="https://example.com/"
        )

    def delete(self, redirect_id):
        return self.client.delete(
            reverse(
                "wagtailapi_v3:delete_redirect", kwargs={"redirect_id": redirect_id}
            )
        )

    def test_anonymous_returns_401(self):
        response = self.delete(self.redirect.pk)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_delete(self):
        self.login()
        pk = self.redirect.pk
        response = self.delete(pk)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Redirect.objects.filter(pk=pk).exists())

    def test_user_without_delete_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.delete(self.redirect.pk)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_delete_permission_can_delete(self):
        user = self.create_user(username="deleter", password="password")
        user.user_permissions.add(Permission.objects.get(codename="delete_redirect"))
        self.login(user)
        response = self.delete(self.redirect.pk)
        self.assertEqual(response.status_code, 204)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.delete(999999)
        self.assert_problem_response(response, status_code=404)
