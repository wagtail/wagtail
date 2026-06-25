import json

from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.models import Page, Site
from wagtail.models.sites import (
    SITE_ROOT_PATHS_CACHE_KEY,
    SITE_ROOT_PATHS_CACHE_VERSION,
)
from wagtail.test.utils import WagtailTestUtils

SITE_FIELDS = {"id", "hostname", "port", "site_name", "root_page_id", "is_default_site"}


class TestV3SiteListing(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_sites"), params)

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
        for site in content["items"]:
            self.assertEqual(set(site.keys()), SITE_FIELDS)

    def test_count_matches_database(self):
        self.login()
        content = self.get_response().json()
        self.assertEqual(content["count"], Site.objects.count())

    def test_default_limit_is_20(self):
        self.login()
        content = self.get_response().json()
        self.assertLessEqual(len(content["items"]), 20)

    def test_user_with_any_site_permission_can_list(self):
        user = self.create_user(username="viewer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="view_site"))
        self.login(username="viewer", password="password")
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_user_without_any_site_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.get_response()
        self.assert_problem_response(response, status_code=403)


class TestV3SiteDetail(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, site_id):
        return self.client.get(
            reverse("wagtailapi_v3:detail_site", kwargs={"site_id": site_id})
        )

    def test_anonymous_returns_401(self):
        site = Site.objects.get(is_default_site=True)
        response = self.get_response(site.pk)
        self.assert_problem_response(response, status_code=401)

    def test_detail_returns_correct_fields(self):
        self.login()
        site = Site.objects.get(is_default_site=True)
        response = self.get_response(site.pk)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(set(content.keys()), SITE_FIELDS)
        self.assertEqual(content["id"], site.pk)
        self.assertEqual(content["hostname"], site.hostname)
        self.assertEqual(content["port"], site.port)
        self.assertEqual(content["root_page_id"], site.root_page_id)
        self.assertEqual(content["is_default_site"], True)

    def test_user_without_any_site_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        site = Site.objects.get(is_default_site=True)
        response = self.get_response(site.pk)
        self.assert_problem_response(response, status_code=403)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.get_response(999999)
        self.assert_problem_response(response, status_code=404)


class TestV3SiteCreate(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.valid_payload = {
            "hostname": "new.example.com",
            "port": 80,
            "site_name": "New Site",
            "root_page_id": self.root_page.pk,
            "is_default_site": False,
        }

    def post(self, data):
        return self.client.post(
            reverse("wagtailapi_v3:create_site"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create(self):
        self.login()
        initial_count = Site.objects.count()
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Site.objects.count(), initial_count + 1)
        content = response.json()
        self.assertEqual(set(content.keys()), SITE_FIELDS)
        self.assertEqual(content["hostname"], "new.example.com")

    def test_user_without_add_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.post(self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_add_permission_can_create(self):
        user = self.create_user(username="adder", password="password")
        user.user_permissions.add(Permission.objects.get(codename="add_site"))
        self.login(user)
        response = self.post(self.valid_payload)
        self.assertEqual(response.status_code, 201)

    def test_duplicate_hostname_port_returns_422(self):
        self.login()
        existing = Site.objects.get(is_default_site=True)
        payload = dict(self.valid_payload)
        payload["hostname"] = existing.hostname
        payload["port"] = existing.port
        response = self.post(payload)
        self.assert_problem_response(response, status_code=422)

    def test_two_default_sites_returns_422(self):
        self.login()
        payload = dict(self.valid_payload)
        payload["is_default_site"] = True
        response = self.post(payload)
        self.assert_problem_response(response, status_code=422)

    def test_invalid_root_page_id_returns_422(self):
        self.login()
        payload = dict(self.valid_payload)
        payload["root_page_id"] = 999999
        response = self.post(payload)
        self.assert_problem_response(response, status_code=422)

    def test_create_invalidates_site_root_paths_cache(self):
        self.login()
        # Warm the cache.
        Site.get_site_root_paths()

        self.assertIsNotNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )
        self.post(self.valid_payload)
        self.assertIsNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )

    def test_hostname_is_lowercased(self):
        self.login()
        payload = dict(self.valid_payload)
        payload["hostname"] = "UPPER.Example.COM"
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        content = response.json()
        self.assertEqual(content["hostname"], "upper.example.com")


class TestV3SiteUpdate(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def setUp(self):
        super().setUp()
        self.site = Site.objects.get(is_default_site=True)
        self.root_page = Page.objects.get(depth=1)
        self.valid_payload = {
            "hostname": "updated.example.com",
            "port": 80,
            "site_name": "Updated",
            "root_page_id": self.site.root_page_id,
            "is_default_site": True,
        }

    def put(self, site_id, data):
        return self.client.put(
            reverse("wagtailapi_v3:update_site", kwargs={"site_id": site_id}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        response = self.put(self.site.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update(self):
        self.login()
        response = self.put(self.site.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)
        self.site.refresh_from_db()
        self.assertEqual(self.site.hostname, "updated.example.com")

    def test_user_without_change_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.put(self.site.pk, self.valid_payload)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_change_permission_can_update(self):
        user = self.create_user(username="changer", password="password")
        user.user_permissions.add(Permission.objects.get(codename="change_site"))
        self.login(username="changer", password="password")
        response = self.put(self.site.pk, self.valid_payload)
        self.assertEqual(response.status_code, 200)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.put(999999, self.valid_payload)
        self.assert_problem_response(response, status_code=404)

    def test_is_default_site_conflict_returns_422(self):
        # Create a second non-default site, then try to make it default
        # while the first is still default.
        second = Site.objects.create(
            hostname="second.example.com",
            port=80,
            root_page=self.root_page,
            is_default_site=False,
        )
        self.login()
        payload = {
            "hostname": "second.example.com",
            "port": 80,
            "site_name": "",
            "root_page_id": self.root_page.pk,
            "is_default_site": True,
        }
        response = self.put(second.pk, payload)
        self.assert_problem_response(response, status_code=422)

    def test_update_invalidates_site_root_paths_cache(self):
        self.login()
        Site.get_site_root_paths()

        self.assertIsNotNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )
        self.put(self.site.pk, self.valid_payload)
        self.assertIsNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )

    def test_response_fields(self):
        self.login()
        response = self.put(self.site.pk, self.valid_payload)
        content = response.json()
        self.assertEqual(set(content.keys()), SITE_FIELDS)


class TestV3SiteDelete(TestV3Base, WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def setUp(self):
        super().setUp()
        root_page = Page.objects.get(depth=1)
        self.site_to_delete = Site.objects.create(
            hostname="todelete.example.com",
            port=80,
            site_name="To Delete",
            root_page=root_page,
            is_default_site=False,
        )

    def delete(self, site_id):
        return self.client.delete(
            reverse("wagtailapi_v3:delete_site", kwargs={"site_id": site_id})
        )

    def test_anonymous_returns_401(self):
        response = self.delete(self.site_to_delete.pk)
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_delete(self):
        self.login()
        pk = self.site_to_delete.pk
        response = self.delete(pk)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Site.objects.filter(pk=pk).exists())

    def test_user_without_delete_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.delete(self.site_to_delete.pk)
        self.assert_problem_response(response, status_code=403)

    def test_user_with_delete_permission_can_delete(self):
        user = self.create_user(username="deleter", password="password")
        user.user_permissions.add(Permission.objects.get(codename="delete_site"))
        self.login(user)
        response = self.delete(self.site_to_delete.pk)
        self.assertEqual(response.status_code, 204)

    def test_unknown_id_returns_404(self):
        self.login()
        response = self.delete(999999)
        self.assert_problem_response(response, status_code=404)

    def test_delete_invalidates_site_root_paths_cache(self):
        self.login()
        Site.get_site_root_paths()

        self.assertIsNotNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )
        self.delete(self.site_to_delete.pk)
        self.assertIsNone(
            cache.get(SITE_ROOT_PATHS_CACHE_KEY, version=SITE_ROOT_PATHS_CACHE_VERSION)
        )
