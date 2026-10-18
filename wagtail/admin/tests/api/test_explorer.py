import datetime
from http import HTTPStatus

from django.contrib.auth.models import Group, Permission
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from wagtail import hooks
from wagtail.models import (
    GroupPagePermission,
    Locale,
    get_default_page_content_type,
)
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import Page, PageFixturesMixin, WagtailTestUtils

LISTING_META_KEYS = {
    "type",
    "locale",
    "depth",
    "status",
    "live",
    "has_unpublished_changes",
    "has_children",
}


class ExplorerAPITestMixin(PageFixturesMixin, WagtailTestUtils):
    fixtures = ["demosite.json"]

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def get(self, page_id, **params):
        return self.client.get(
            reverse("wagtailadmin_api:explorer", kwargs={"page_id": page_id}),
            params,
        )

    def get_child_ids(self, content):
        return [page["id"] for page in content["children"]["items"]]

    def make_simple_page(self, parent, title, **kwargs):
        return parent.add_child(
            instance=SimplePage(title=title, content="Simple page", **kwargs)
        )

    def grant_page_permission(self, user, page, codename):
        group = Group.objects.create(name=f"{page.title} {codename}")
        GroupPagePermission.objects.create(
            group=group,
            page=page,
            permission=Permission.objects.get(
                content_type=get_default_page_content_type(),
                codename=codename,
            ),
        )
        user.groups.add(group)

    def login_as_admin_only_user(self):
        user = self.create_user(username="basic_user")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            )
        )
        self.client.force_login(user)
        return user


class TestExplorerPage(ExplorerAPITestMixin, TestCase):
    def test_basic(self):
        response = self.get(4)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        content = response.json()
        self.assertEqual(set(content.keys()), {"page", "translations", "children"})

        page = content["page"]
        self.assertEqual(
            set(page.keys()), {"id", "title", "admin_display_title", "meta"}
        )
        self.assertEqual(set(page["meta"].keys()), LISTING_META_KEYS | {"parent"})
        self.assertEqual(page["id"], 4)
        self.assertEqual(page["title"], "Events index")
        self.assertEqual(page["admin_display_title"], "Events index")
        self.assertEqual(page["meta"]["type"], "demosite.EventIndexPage")
        self.assertEqual(page["meta"]["locale"], "en")
        self.assertEqual(page["meta"]["depth"], 3)
        self.assertEqual(page["meta"]["status"], "live")
        self.assertIs(page["meta"]["live"], True)
        self.assertIs(page["meta"]["has_unpublished_changes"], False)
        self.assertIs(page["meta"]["has_children"], True)
        self.assertEqual(page["meta"]["parent"]["id"], 2)
        self.assertEqual(page["meta"]["parent"]["title"], "Home page")
        self.assertEqual(page["meta"]["parent"]["meta"], {"type": "demosite.HomePage"})

        self.assertEqual(content["translations"], [])

    def test_top_level_page_has_root_as_parent(self):
        response = self.get(2)

        page = response.json()["page"]
        self.assertEqual(page["meta"]["depth"], 2)
        self.assertEqual(page["meta"]["parent"]["id"], 1)

    def test_root_page(self):
        response = self.get(1)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        content = response.json()
        self.assertEqual(content["page"]["id"], 1)
        self.assertEqual(content["page"]["meta"]["depth"], 1)
        self.assertIsNone(content["page"]["meta"]["parent"])
        self.assertIs(content["page"]["meta"]["has_children"], True)
        self.assertEqual(self.get_child_ids(content), [2, 24])

    def test_nonexistent_page(self):
        response = self.get(999)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_not_logged_in(self):
        self.client.logout()
        url = reverse("wagtailadmin_api:explorer", kwargs={"page_id": 2})

        response = self.client.get(url)

        self.assertRedirects(response, reverse("wagtailadmin_login") + "?next=" + url)


class TestExplorerChildren(ExplorerAPITestMixin, TestCase):
    def test_children(self):
        response = self.get(2)

        children = response.json()["children"]
        self.assertEqual(children["count"], 5)
        self.assertEqual([page["id"] for page in children["items"]], [4, 5, 6, 20, 12])

    def test_child_shape(self):
        response = self.get(2)

        item = response.json()["children"]["items"][0]
        self.assertEqual(
            set(item.keys()), {"id", "title", "admin_display_title", "meta"}
        )
        # parent is only available for the explorer's current page
        self.assertEqual(set(item["meta"].keys()), LISTING_META_KEYS)
        self.assertEqual(item["id"], 4)
        self.assertEqual(item["admin_display_title"], "Events index")
        self.assertEqual(item["meta"]["depth"], 3)

    def test_has_children(self):
        response = self.get(2)

        has_children = {
            item["id"]: item["meta"]["has_children"]
            for item in response.json()["children"]["items"]
        }
        self.assertEqual(has_children, {4: True, 5: True, 6: True, 20: True, 12: False})

    def test_status(self):
        Page.objects.get(id=4).specific.save_revision()
        Page.objects.get(id=5).unpublish()
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        Page.objects.get(id=6).unpublish()
        Page.objects.get(id=6).specific.save_revision(approved_go_live_at=tomorrow)
        Page.objects.get(id=20).unpublish()
        Page.objects.filter(id=20).update(expired=True)

        response = self.get(2)

        statuses = {
            item["id"]: (
                item["meta"]["status"],
                item["meta"]["live"],
                item["meta"]["has_unpublished_changes"],
            )
            for item in response.json()["children"]["items"]
        }
        self.assertEqual(
            statuses,
            {
                4: ("live + draft", True, True),
                5: ("draft", False, True),
                6: ("scheduled", False, True),
                20: ("expired", False, True),
                12: ("live", True, False),
            },
        )

    def test_unpublished_and_private_pages_are_included(self):
        Page.objects.get(id=16).unpublish()
        Page.objects.get(id=18).view_restrictions.create(password="test")

        response = self.get(5)

        self.assertEqual(self.get_child_ids(response.json()), [16, 18, 19])

    def test_no_children(self):
        response = self.get(12)

        self.assertEqual(response.json()["children"], {"count": 0, "items": []})

    def test_construct_explorer_page_queryset_hooks(self):
        movies = self.make_simple_page(Page.objects.get(pk=1), "Movies")
        visible_movies = [
            self.make_simple_page(movies, "The Way of the Dragon"),
            self.make_simple_page(movies, "Enter the Dragon"),
            self.make_simple_page(movies, "Dragons Forever"),
        ]
        # Hidden by the hide_hidden_pages hook in wagtail.test.testapp
        self.make_simple_page(movies, "The Hidden Fortress")
        self.make_simple_page(movies, "Crouching Tiger, Hidden Dragon")

        response = self.get(movies.pk)

        content = response.json()
        self.assertEqual(content["children"]["count"], 3)
        self.assertEqual(
            self.get_child_ids(content), [page.pk for page in visible_movies]
        )

    def test_construct_explorer_page_queryset_hooks_receive_parent_page(self):
        received = []

        def hook(parent_page, pages, request):
            received.append(parent_page)
            return pages.order_by("-title")

        with hooks.register_temporarily("construct_explorer_page_queryset", hook):
            response = self.get(2)

        # Same as the admin's page listing view, the specific page is passed
        self.assertEqual(received, [Page.objects.get(pk=2).specific])
        self.assertEqual(self.get_child_ids(response.json()), [6, 20, 4, 12, 5])

    def test_construct_explorer_page_queryset_hooks_ordering(self):
        parent = self.make_simple_page(Page.objects.get(pk=2), "Parent")
        children = [
            self.make_simple_page(parent, f"Child {i:02}").pk for i in range(55)
        ]

        def hook(parent_page, pages, request):
            return pages.order_by("-title")

        with hooks.register_temporarily("construct_explorer_page_queryset", hook):
            first_response = self.get(parent.pk)
            second_response = self.get(parent.pk, offset=50)

        # The hook's ordering is kept, including across paginated responses
        children.reverse()
        self.assertEqual(self.get_child_ids(first_response.json()), children[:50])
        self.assertEqual(self.get_child_ids(second_response.json()), children[50:])

    def test_pagination(self):
        parent = self.make_simple_page(Page.objects.get(pk=2), "Parent")
        children = [self.make_simple_page(parent, f"Child {i}").pk for i in range(55)]

        response = self.get(parent.pk)
        content = response.json()
        self.assertEqual(content["children"]["count"], 55)
        # Default limit is 50, matching the page listing view
        self.assertEqual(self.get_child_ids(content), children[:50])

        response = self.get(parent.pk, offset=50)
        self.assertEqual(self.get_child_ids(response.json()), children[50:])

        response = self.get(parent.pk, limit=5, offset=5)
        self.assertEqual(self.get_child_ids(response.json()), children[5:10])

    def test_limit_max(self):
        response = self.get(2, limit=51)
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)

    @override_settings(WAGTAILAPI_LIMIT_MAX=2)
    def test_not_affected_by_public_api_limit_max(self):
        response = self.get(2)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.get_child_ids(response.json()), [4, 5, 6, 20, 12])

    def test_invalid_offset(self):
        response = self.get(2, offset=-1)
        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)

    def test_query_count_does_not_grow_with_children(self):
        parent = self.make_simple_page(Page.objects.get(pk=2), "Parent")
        for i in range(2):
            self.make_simple_page(parent, f"Child {i}", live=False)

        def count_queries():
            with CaptureQueriesContext(connection) as context:
                response = self.get(parent.pk)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            return len(context.captured_queries)

        # Warm up caches, e.g. site root paths
        count_queries()
        num_queries = count_queries()

        for i in range(2, 10):
            self.make_simple_page(parent, f"Child {i}", live=False)

        self.assertEqual(count_queries(), num_queries)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestExplorerTranslations(ExplorerAPITestMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.french = Locale.objects.create(language_code="fr")
        self.homepage = Page.objects.get(pk=2)
        self.french_homepage = self.homepage.copy_for_translation(self.french)

    def test_translations(self):
        # copy_for_translation doesn't copy children, so give the French
        # homepage a child to make it navigable in the explorer
        self.make_simple_page(self.french_homepage, "Accueil enfant")

        response = self.get(self.homepage.pk)
        self.assertEqual(
            response.json()["translations"],
            [{"id": self.french_homepage.pk, "locale": "fr"}],
        )

        response = self.get(self.french_homepage.pk)
        self.assertEqual(
            response.json()["translations"],
            [{"id": self.homepage.pk, "locale": "en"}],
        )

    def test_translations_without_children_are_excluded(self):
        response = self.get(self.homepage.pk)
        self.assertEqual(response.json()["translations"], [])

    def test_root_page_has_no_translations(self):
        response = self.get(1)
        self.assertEqual(response.json()["translations"], [])

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_i18n_disabled(self):
        self.make_simple_page(self.french_homepage, "Accueil enfant")

        response = self.get(self.homepage.pk)
        self.assertEqual(response.json()["translations"], [])


class TestExplorerPermissions(ExplorerAPITestMixin, TestCase):
    def test_without_page_permissions(self):
        self.login_as_admin_only_user()

        response = self.get(2)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_with_page_permission(self):
        user = self.login_as_admin_only_user()
        self.grant_page_permission(
            user,
            Page.objects.get(pk=5),
            Page.PERMISSION_CODENAMES.CHANGE,
        )

        # Only the pages below the first common ancestor of the pages with
        # permission are explorable
        response = self.get(1)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # Siblings of the page with permission are not explorable
        response = self.get(2)
        self.assertEqual(self.get_child_ids(response.json()), [5])

        # The parent of the explorable root page is not explorable, so it is
        # not included
        self.assertIsNone(response.json()["page"]["meta"]["parent"])

        # Descendants of the page with permission are explorable
        response = self.get(5)
        self.assertEqual(response.json()["page"]["meta"]["parent"]["id"], 2)
        self.assertEqual(self.get_child_ids(response.json()), [16, 18, 19])

        # Pages that are not explorable give a 404
        response = self.get(4)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestCustomAdminDisplayTitle(PageFixturesMixin, WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.login()
        self.event_page = Page.objects.get(url_path="/home/events/saint-patrick/")

    def get(self, page_id):
        return self.client.get(
            reverse("wagtailadmin_api:explorer", kwargs={"page_id": page_id})
        )

    def test_custom_admin_display_title_shown_on_page(self):
        content = self.get(self.event_page.pk).json()

        self.assertEqual(content["page"]["title"], "Saint Patrick")
        self.assertEqual(
            content["page"]["admin_display_title"], "Saint Patrick (single event)"
        )

    def test_custom_admin_display_title_shown_on_children(self):
        content = self.get(self.event_page.get_parent().pk).json()

        matching_items = [
            item
            for item in content["children"]["items"]
            if item["id"] == self.event_page.pk
        ]
        self.assertEqual(len(matching_items), 1)
        self.assertEqual(matching_items[0]["title"], "Saint Patrick")
        self.assertEqual(
            matching_items[0]["admin_display_title"], "Saint Patrick (single event)"
        )
