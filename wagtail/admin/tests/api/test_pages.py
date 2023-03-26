import collections
import datetime
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from wagtail import hooks
from wagtail.api.v2.tests.test_pages import (
    TestPageDetail,
    TestPageListing,
    TestPageListingSearch,
)
from wagtail.models import GroupPagePermission, Locale, Page, PageLogEntry
from wagtail.test.demosite import models
from wagtail.test.testapp.models import (
    EventIndex,
    EventPage,
    PageWithExcludedCopyField,
    SimplePage,
    StreamPage,
)
from wagtail.users.models import UserProfile

from .utils import AdminAPITestCase


def get_total_page_count():
    # Need to take away 1 as the root page is invisible over the API by default
    return Page.objects.count() - 1


class TestAdminPageListing(AdminAPITestCase, TestPageListing):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailadmin_api:pages:listing"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_homepage(self):
        return Page.objects.get(slug="home-page")

    # BASIC TESTS

    def test_basic(self):
        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        # Check that the meta section is there
        self.assertIn("meta", content)
        self.assertIsInstance(content["meta"], dict)

        # Check that the total count is there and correct
        self.assertIn("total_count", content["meta"])
        self.assertIsInstance(content["meta"]["total_count"], int)
        self.assertEqual(content["meta"]["total_count"], get_total_page_count())

        # Check that the items section is there
        self.assertIn("items", content)
        self.assertIsInstance(content["items"], list)

        # Check that each page has a meta section with type, detail_url, html_url, status and children attributes
        for page in content["items"]:
            self.assertIn("meta", page)
            self.assertIsInstance(page["meta"], dict)
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "html_url",
                    "status",
                    "children",
                    "slug",
                    "first_published_at",
                    "latest_revision_created_at",
                },
            )

        # Check the type info
        self.assertIsInstance(content["__types"], dict)
        self.assertEqual(
            set(content["__types"].keys()),
            {
                "demosite.EventPage",
                "demosite.StandardIndexPage",
                "demosite.PersonPage",
                "demosite.HomePage",
                "demosite.StandardPage",
                "demosite.EventIndexPage",
                "demosite.ContactPage",
                "demosite.BlogEntryPage",
                "demosite.BlogIndexPage",
            },
        )
        self.assertEqual(
            set(content["__types"]["demosite.EventPage"].keys()),
            {"verbose_name", "verbose_name_plural"},
        )
        self.assertEqual(
            content["__types"]["demosite.EventPage"]["verbose_name"], "event page"
        )
        self.assertEqual(
            content["__types"]["demosite.EventPage"]["verbose_name_plural"],
            "event pages",
        )

    # Not applicable to the admin API
    test_unpublished_pages_dont_appear_in_list = None
    test_private_pages_dont_appear_in_list = None

    def test_unpublished_pages_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(content["meta"]["total_count"], total_count)

    def test_private_pages_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(password="test")

        new_total_count = get_total_page_count()
        self.assertEqual(total_count, total_count)

        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(content["meta"]["total_count"], new_total_count)

    def test_get_in_non_content_language(self):
        # set logged-in user's admin UI language to Swedish
        user = get_user_model().objects.get(email="test@email.com")
        UserProfile.objects.update_or_create(
            user=user, defaults={"preferred_language": "se"}
        )

        response = self.get_response()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))
        self.assertIn("meta", content)

    # FIELDS

    # Not applicable to the admin API
    test_parent_field_gives_error = None

    def test_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title,date,feed_image"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()),
                {"id", "meta", "title", "admin_display_title", "date", "feed_image"},
            )

    def test_fields_default(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()), {"id", "meta", "title", "admin_display_title"}
            )
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "html_url",
                    "children",
                    "status",
                    "slug",
                    "first_published_at",
                    "latest_revision_created_at",
                },
            )

    def test_remove_meta_fields(self):
        response = self.get_response(fields="-html_url")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()), {"id", "meta", "title", "admin_display_title"}
            )
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "slug",
                    "first_published_at",
                    "latest_revision_created_at",
                    "status",
                    "children",
                },
            )

    def test_remove_all_meta_fields(self):
        response = self.get_response(
            fields="-type,-detail_url,-slug,-first_published_at,-html_url,-latest_revision_created_at,-status,-children"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "title", "admin_display_title"})

    def test_remove_fields(self):
        response = self.get_response(fields="-title,-admin_display_title")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta"})

    def test_remove_id_field(self):
        response = self.get_response(fields="-id")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"meta", "title", "admin_display_title"})

    def test_all_fields(self):
        response = self.get_response(type="demosite.BlogEntryPage", fields="*")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()),
                {
                    "id",
                    "meta",
                    "title",
                    "admin_display_title",
                    "date",
                    "related_links",
                    "tags",
                    "carousel_items",
                    "body",
                    "feed_image",
                    "feed_image_thumbnail",
                },
            )
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "show_in_menus",
                    "first_published_at",
                    "seo_title",
                    "slug",
                    "parent",
                    "html_url",
                    "search_description",
                    "locale",
                    "alias_of",
                    "children",
                    "descendants",
                    "ancestors",
                    "translations",
                    "status",
                    "latest_revision_created_at",
                },
            )

    def test_all_fields_then_remove_something(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            fields="*,-title,-admin_display_title,-date,-seo_title,-status",
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()),
                {
                    "id",
                    "meta",
                    "related_links",
                    "tags",
                    "carousel_items",
                    "body",
                    "feed_image",
                    "feed_image_thumbnail",
                },
            )
            self.assertEqual(
                set(page["meta"].keys()),
                {
                    "type",
                    "detail_url",
                    "show_in_menus",
                    "first_published_at",
                    "slug",
                    "parent",
                    "html_url",
                    "search_description",
                    "locale",
                    "alias_of",
                    "children",
                    "descendants",
                    "ancestors",
                    "translations",
                    "latest_revision_created_at",
                },
            )

    def test_all_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(*)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page["feed_image"].keys()),
                {"id", "meta", "title", "width", "height", "thumbnail"},
            )

    def test_fields_foreign_key(self):
        # Only the base the detail_url is different here from the public API
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title,date,feed_image"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            feed_image = page["feed_image"]

            if feed_image is not None:
                self.assertIsInstance(feed_image, dict)
                self.assertEqual(set(feed_image.keys()), {"id", "meta", "title"})
                self.assertIsInstance(feed_image["id"], int)
                self.assertIsInstance(feed_image["meta"], dict)
                self.assertEqual(
                    set(feed_image["meta"].keys()),
                    {"type", "detail_url", "download_url"},
                )
                self.assertEqual(feed_image["meta"]["type"], "wagtailimages.Image")
                self.assertEqual(
                    feed_image["meta"]["detail_url"],
                    "http://localhost/admin/api/main/images/%d/" % feed_image["id"],
                )

    def test_fields_parent(self):
        response = self.get_response(type="demosite.BlogEntryPage", fields="parent")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            parent = page["meta"]["parent"]

            # All blog entry pages have the same parent
            self.assertDictEqual(
                parent,
                {
                    "id": 5,
                    "meta": {
                        "type": "demosite.BlogIndexPage",
                        "detail_url": "http://localhost/admin/api/main/pages/5/",
                        "html_url": "http://localhost/blog-index/",
                    },
                    "title": "Blog index",
                },
            )

    def test_fields_descendants(self):
        response = self.get_response(fields="descendants")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            descendants = page["meta"]["descendants"]
            self.assertEqual(set(descendants.keys()), {"count", "listing_url"})
            self.assertIsInstance(descendants["count"], int)
            self.assertEqual(
                descendants["listing_url"],
                "http://localhost/admin/api/main/pages/?descendant_of=%d" % page["id"],
            )

    def test_fields_child_relation(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title,related_links"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()),
                {"id", "meta", "title", "admin_display_title", "related_links"},
            )
            self.assertIsInstance(page["related_links"], list)

    def test_fields_ordering(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="date,title,feed_image,related_links"
        )

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(
            response.content.decode("UTF-8")
        )
        field_order = [
            "id",
            "meta",
            "title",
            "admin_display_title",
            "date",
            "feed_image",
            "related_links",
        ]
        self.assertEqual(list(content["items"][0].keys()), field_order)

    def test_fields_tags(self):
        response = self.get_response(type="demosite.BlogEntryPage", fields="tags")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()), {"id", "meta", "tags", "title", "admin_display_title"}
            )
            self.assertIsInstance(page["tags"], list)

    def test_fields_translations(self):
        # Add a translation of the homepage
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)

        response = self.get_response(fields="translations")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            translations = page["meta"]["translations"]

            if page["id"] == homepage.id:
                self.assertEqual(len(translations), 1)
                self.assertEqual(translations[0]["id"], french_homepage.id)
                self.assertEqual(translations[0]["meta"]["locale"], "fr")

            elif page["id"] == french_homepage.id:
                self.assertEqual(len(translations), 1)
                self.assertEqual(translations[0]["id"], homepage.id)
                self.assertEqual(translations[0]["meta"]["locale"], "en")

            else:
                self.assertEqual(translations, [])

    # CHILD OF FILTER

    # Not applicable to the admin API
    test_child_of_page_thats_not_in_same_site_gives_error = None

    def test_child_of_root(self):
        # Only return the homepage as that's the only child of the "root" node
        # in the tree. This is different to the public API which pretends the
        # homepage of the current site is the root page.
        response = self.get_response(child_of="root")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 24])

    def test_child_of_page_1(self):
        # Public API doesn't allow this, as it's the root page
        response = self.get_response(child_of=1)
        json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 200)

    # DESCENDANT OF FILTER

    # Not applicable to the admin API
    test_descendant_of_page_thats_not_in_same_site_gives_error = None

    def test_descendant_of_root(self):
        response = self.get_response(descendant_of="root")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [2, 4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12, 24],
        )

    def test_descendant_of_root_doesnt_give_error(self):
        # Public API doesn't allow this
        response = self.get_response(descendant_of=1)
        json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 200)

    # FOR EXPLORER FILTER

    def make_simple_page(self, parent, title):
        return parent.add_child(instance=SimplePage(title=title, content="Simple page"))

    def test_for_explorer_filter(self):
        movies = self.make_simple_page(Page.objects.get(pk=1), "Movies")
        visible_movies = [
            self.make_simple_page(movies, "The Way of the Dragon"),
            self.make_simple_page(movies, "Enter the Dragon"),
            self.make_simple_page(movies, "Dragons Forever"),
        ]
        hidden_movies = [
            self.make_simple_page(movies, "The Hidden Fortress"),
            self.make_simple_page(movies, "Crouching Tiger, Hidden Dragon"),
            self.make_simple_page(
                movies, "Crouching Tiger, Hidden Dragon: Sword of Destiny"
            ),
        ]

        response = self.get_response(child_of=movies.pk, for_explorer=1)
        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [page.pk for page in visible_movies])

        response = self.get_response(child_of=movies.pk)
        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list, [page.pk for page in visible_movies + hidden_movies]
        )

    def test_for_explorer_no_child_of(self):
        response = self.get_response(for_explorer=1)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(
            content,
            {
                "message": "filtering by for_explorer without child_of is not supported",
            },
        )

    def test_for_explorer_construct_explorer_page_queryset_ordering(self):
        def set_custom_ordering(parent_page, pages, request):
            return pages.order_by("-title")

        with hooks.register_temporarily(
            "construct_explorer_page_queryset", set_custom_ordering
        ):
            response = self.get_response(for_explorer=True, child_of=2)

        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [6, 20, 4, 12, 5])

    # HAS CHILDREN FILTER

    def test_has_children_filter(self):
        response = self.get_response(has_children="true")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 5, 6, 21, 20, 24])

    def test_has_children_filter_off(self):
        response = self.get_response(has_children="false")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list, [8, 9, 16, 18, 19, 10, 15, 17, 22, 23, 13, 14, 12, 25]
        )

    def test_has_children_filter_int(self):
        response = self.get_response(has_children=1)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 4, 5, 6, 21, 20, 24])

    def test_has_children_filter_int_off(self):
        response = self.get_response(has_children=0)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list, [8, 9, 16, 18, 19, 10, 15, 17, 22, 23, 13, 14, 12, 25]
        )

    def test_has_children_filter_invalid_integer(self):
        response = self.get_response(has_children=3)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "has_children must be 'true' or 'false'"})

    def test_has_children_filter_invalid_value(self):
        response = self.get_response(has_children="yes")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "has_children must be 'true' or 'false'"})

    # TYPE FILTER

    def test_type_filter_items_are_all_blog_entries(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(page["meta"]["type"], "demosite.BlogEntryPage")

            # No specific fields available by default
            self.assertEqual(
                set(page.keys()), {"id", "meta", "title", "admin_display_title"}
            )

    def test_type_filter_multiple(self):
        response = self.get_response(type="demosite.BlogEntryPage,demosite.EventPage")
        content = json.loads(response.content.decode("UTF-8"))

        blog_page_seen = False
        event_page_seen = False

        for page in content["items"]:
            self.assertIn(
                page["meta"]["type"], ["demosite.BlogEntryPage", "demosite.EventPage"]
            )

            if page["meta"]["type"] == "demosite.BlogEntryPage":
                blog_page_seen = True
            elif page["meta"]["type"] == "demosite.EventPage":
                event_page_seen = True

            # Only generic fields available
            self.assertEqual(
                set(page.keys()), {"id", "meta", "title", "admin_display_title"}
            )

        self.assertTrue(blog_page_seen, msg="No blog pages were found in the items")
        self.assertTrue(event_page_seen, msg="No event pages were found in the items")

    # Not applicable to the admin API
    test_site_filter_same_hostname_returns_error = None
    test_site_filter = None

    def test_ordering_default(self):
        # overridden because the admin API lists all pages, regardless of sites

        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [2, 4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12, 24],
        )

    def test_ordering_by_title(self):
        # overridden because the admin API lists all pages, regardless of sites

        response = self.get_response(order="title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [21, 22, 19, 23, 5, 16, 18, 12, 14, 8, 9, 4, 25, 2, 24, 13, 20, 17, 6, 10],
        )

    def test_ordering_by_title_backwards(self):
        # overridden because the admin API lists all pages, regardless of sites

        response = self.get_response(order="-title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [15, 10, 6, 17, 20, 13, 24, 2, 25, 4, 9, 8, 14, 12, 18, 16, 5, 23, 19, 22],
        )

    def test_limit_total_count(self):
        # overridden because the admin API lists all pages, regardless of sites
        # the function is actually unchanged, but uses a different total page count helper

        response = self.get_response(limit=2)
        content = json.loads(response.content.decode("UTF-8"))

        # The total count must not be affected by "limit"
        self.assertEqual(content["meta"]["total_count"], get_total_page_count())

    def test_offset_total_count(self):
        # overridden because the admin API lists all pages, regardless of sites
        # the function is actually unchanged, but uses a different total page count helper

        response = self.get_response(offset=10)
        content = json.loads(response.content.decode("UTF-8"))

        # The total count must not be affected by "offset"
        self.assertEqual(content["meta"]["total_count"], get_total_page_count())

    @override_settings(WAGTAILAPI_LIMIT_MAX=None)
    def test_limit_max_none_gives_no_errors(self):
        # overridden because the admin API lists all pages, regardless of sites
        # the function is actually unchanged, but uses a different total page count helper

        response = self.get_response(limit=1000000)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(content["items"]), get_total_page_count())


class TestAdminPageDetail(AdminAPITestCase, TestPageDetail):
    fixtures = ["demosite.json"]

    def get_response(self, page_id, **params):
        return self.client.get(
            reverse("wagtailadmin_api:pages:detail", args=(page_id,)), params
        )

    def test_basic(self):
        response = self.get_response(16)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        # Check the id field
        self.assertIn("id", content)
        self.assertEqual(content["id"], 16)

        # Check that the meta section is there
        self.assertIn("meta", content)
        self.assertIsInstance(content["meta"], dict)

        # Check the meta type
        self.assertIn("type", content["meta"])
        self.assertEqual(content["meta"]["type"], "demosite.BlogEntryPage")

        # Check the meta detail_url
        self.assertIn("detail_url", content["meta"])
        self.assertEqual(
            content["meta"]["detail_url"], "http://localhost/admin/api/main/pages/16/"
        )

        # Check the meta html_url
        self.assertIn("html_url", content["meta"])
        self.assertEqual(
            content["meta"]["html_url"], "http://localhost/blog-index/blog-post/"
        )

        # Check the meta status

        self.assertIn("status", content["meta"])
        self.assertEqual(
            content["meta"]["status"],
            {"status": "live", "live": True, "has_unpublished_changes": False},
        )

        # Check the meta children

        self.assertIn("children", content["meta"])
        self.assertEqual(
            content["meta"]["children"],
            {
                "count": 0,
                "listing_url": "http://localhost/admin/api/main/pages/?child_of=16",
            },
        )

        # Check the parent field
        self.assertIn("parent", content["meta"])
        self.assertIsInstance(content["meta"]["parent"], dict)
        self.assertEqual(set(content["meta"]["parent"].keys()), {"id", "meta", "title"})
        self.assertEqual(content["meta"]["parent"]["id"], 5)
        self.assertIsInstance(content["meta"]["parent"]["meta"], dict)
        self.assertEqual(
            set(content["meta"]["parent"]["meta"].keys()),
            {"type", "detail_url", "html_url"},
        )
        self.assertEqual(
            content["meta"]["parent"]["meta"]["type"], "demosite.BlogIndexPage"
        )
        self.assertEqual(
            content["meta"]["parent"]["meta"]["detail_url"],
            "http://localhost/admin/api/main/pages/5/",
        )
        self.assertEqual(
            content["meta"]["parent"]["meta"]["html_url"],
            "http://localhost/blog-index/",
        )

        # Check the alias_of field
        # See test_alias_page for a test on an alias page
        self.assertIn("alias_of", content["meta"])
        self.assertIsNone(content["meta"]["alias_of"])

        # Check that the custom fields are included
        self.assertIn("date", content)
        self.assertIn("body", content)
        self.assertIn("tags", content)
        self.assertIn("feed_image", content)
        self.assertIn("related_links", content)
        self.assertIn("carousel_items", content)

        # Check that the date was serialised properly
        self.assertEqual(content["date"], "2013-12-02")

        # Check that the tags were serialised properly
        self.assertEqual(content["tags"], ["bird", "wagtail"])

        # Check that the feed image was serialised properly
        self.assertIsInstance(content["feed_image"], dict)
        self.assertEqual(set(content["feed_image"].keys()), {"id", "meta", "title"})
        self.assertEqual(content["feed_image"]["id"], 7)
        self.assertIsInstance(content["feed_image"]["meta"], dict)
        self.assertEqual(
            set(content["feed_image"]["meta"].keys()),
            {"type", "detail_url", "download_url"},
        )
        self.assertEqual(content["feed_image"]["meta"]["type"], "wagtailimages.Image")
        self.assertEqual(
            content["feed_image"]["meta"]["detail_url"],
            "http://localhost/admin/api/main/images/7/",
        )

        # Check that the child relations were serialised properly
        self.assertEqual(content["related_links"], [])
        for carousel_item in content["carousel_items"]:
            self.assertEqual(
                set(carousel_item.keys()),
                {"id", "meta", "embed_url", "link", "caption", "image"},
            )
            self.assertEqual(set(carousel_item["meta"].keys()), {"type"})

        # Check the type info
        self.assertIsInstance(content["__types"], dict)
        self.assertEqual(
            set(content["__types"].keys()),
            {
                "wagtailcore.Page",
                "demosite.HomePage",
                "demosite.BlogIndexPage",
                "demosite.BlogEntryPageCarouselItem",
                "demosite.BlogEntryPage",
                "wagtailimages.Image",
            },
        )
        self.assertEqual(
            set(content["__types"]["demosite.BlogIndexPage"].keys()),
            {"verbose_name", "verbose_name_plural"},
        )
        self.assertEqual(
            content["__types"]["demosite.BlogIndexPage"]["verbose_name"],
            "blog index page",
        )
        self.assertEqual(
            content["__types"]["demosite.BlogIndexPage"]["verbose_name_plural"],
            "blog index pages",
        )

    # overridden from public API tests
    def test_meta_parent_id_doesnt_show_root_page(self):
        # Root page is visible in the admin API
        response = self.get_response(2)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIsNotNone(content["meta"]["parent"])

    def test_field_ordering(self):
        # Need to override this as the admin API has a __types field

        response = self.get_response(16)

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        # Test field order
        content = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(
            response.content.decode("UTF-8")
        )
        field_order = [
            "id",
            "meta",
            "title",
            "admin_display_title",
            "body",
            "tags",
            "date",
            "feed_image",
            "feed_image_thumbnail",
            "carousel_items",
            "related_links",
            "__types",
        ]
        self.assertEqual(list(content.keys()), field_order)

    def test_meta_status_draft(self):
        # Unpublish the page
        Page.objects.get(id=16).unpublish()

        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("status", content["meta"])
        self.assertEqual(
            content["meta"]["status"],
            {"status": "draft", "live": False, "has_unpublished_changes": True},
        )

    def test_meta_status_live_draft(self):
        # Save revision without republish
        Page.objects.get(id=16).specific.save_revision()

        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("status", content["meta"])
        self.assertEqual(
            content["meta"]["status"],
            {"status": "live + draft", "live": True, "has_unpublished_changes": True},
        )

    def test_meta_status_scheduled(self):
        # Unpublish and save revision with go live date in the future
        Page.objects.get(id=16).unpublish()
        tomorrow = timezone.now() + datetime.timedelta(days=1)
        Page.objects.get(id=16).specific.save_revision(approved_go_live_at=tomorrow)

        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("status", content["meta"])
        self.assertEqual(
            content["meta"]["status"],
            {"status": "scheduled", "live": False, "has_unpublished_changes": True},
        )

    def test_meta_status_expired(self):
        # Unpublish and set expired flag
        Page.objects.get(id=16).unpublish()
        Page.objects.filter(id=16).update(expired=True)

        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("status", content["meta"])
        self.assertEqual(
            content["meta"]["status"],
            {"status": "expired", "live": False, "has_unpublished_changes": True},
        )

    def test_meta_children_for_parent(self):
        # Homepage should have children
        response = self.get_response(2)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("children", content["meta"])
        self.assertEqual(
            content["meta"]["children"],
            {
                "count": 5,
                "listing_url": "http://localhost/admin/api/main/pages/?child_of=2",
            },
        )

    def test_meta_descendants(self):
        # Homepage should have children
        response = self.get_response(2)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("descendants", content["meta"])
        self.assertEqual(
            content["meta"]["descendants"],
            {
                "count": 18,
                "listing_url": "http://localhost/admin/api/main/pages/?descendant_of=2",
            },
        )

    def test_meta_ancestors(self):
        # Homepage should have children
        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("ancestors", content["meta"])
        self.assertIsInstance(content["meta"]["ancestors"], list)
        self.assertEqual(len(content["meta"]["ancestors"]), 3)
        self.assertEqual(
            content["meta"]["ancestors"][0].keys(),
            {"id", "meta", "title", "admin_display_title"},
        )
        self.assertEqual(content["meta"]["ancestors"][0]["title"], "Root")
        self.assertEqual(content["meta"]["ancestors"][1]["title"], "Home page")
        self.assertEqual(content["meta"]["ancestors"][2]["title"], "Blog index")

    def test_alias_page(self):
        original = Page.objects.get(id=16).specific
        alias = original.create_alias(update_slug="new-slug")

        response = self.get_response(alias.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(content["meta"]["type"], "demosite.BlogEntryPage")
        self.assertEqual(
            content["meta"]["html_url"], "http://localhost/blog-index/new-slug/"
        )

        # Check alias_of field
        self.assertIn("alias_of", content["meta"])
        self.assertIsInstance(content["meta"]["alias_of"], dict)
        self.assertEqual(
            set(content["meta"]["alias_of"].keys()), {"id", "meta", "title"}
        )
        self.assertEqual(content["meta"]["alias_of"]["id"], 16)
        self.assertIsInstance(content["meta"]["alias_of"]["meta"], dict)
        self.assertEqual(
            set(content["meta"]["alias_of"]["meta"].keys()),
            {"type", "detail_url", "html_url"},
        )
        self.assertEqual(
            content["meta"]["alias_of"]["meta"]["type"], "demosite.BlogEntryPage"
        )
        self.assertEqual(
            content["meta"]["alias_of"]["meta"]["detail_url"],
            "http://localhost/admin/api/main/pages/16/",
        )
        self.assertEqual(
            content["meta"]["alias_of"]["meta"]["html_url"],
            "http://localhost/blog-index/blog-post/",
        )

    # FIELDS

    def test_remove_all_meta_fields(self):
        response = self.get_response(
            16,
            fields="-type,-detail_url,-slug,-first_published_at,-html_url,-descendants,-latest_revision_created_at,-alias_of,-children,-ancestors,-show_in_menus,-seo_title,-parent,-status,-search_description",
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertNotIn("meta", set(content.keys()))
        self.assertIn("id", set(content.keys()))

    def test_remove_all_fields(self):
        response = self.get_response(16, fields="_,id,type")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(set(content.keys()), {"id", "meta", "__types"})
        self.assertEqual(set(content["meta"].keys()), {"type"})

    def test_all_nested_fields(self):
        response = self.get_response(16, fields="feed_image(*)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(
            set(content["feed_image"].keys()),
            {"id", "meta", "title", "width", "height", "thumbnail"},
        )

    def test_fields_foreign_key(self):
        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        feed_image = content["feed_image"]

        self.assertIsInstance(feed_image, dict)
        self.assertEqual(set(feed_image.keys()), {"id", "meta", "title"})
        self.assertIsInstance(feed_image["id"], int)
        self.assertIsInstance(feed_image["meta"], dict)
        self.assertEqual(
            set(feed_image["meta"].keys()), {"type", "detail_url", "download_url"}
        )
        self.assertEqual(feed_image["meta"]["type"], "wagtailimages.Image")
        self.assertEqual(
            feed_image["meta"]["detail_url"],
            "http://localhost/admin/api/main/images/%d/" % feed_image["id"],
        )


class TestAdminPageListingSearch(AdminAPITestCase, TestPageListingSearch):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailadmin_api:pages:listing"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_homepage(self):
        return Page.objects.get(slug="home-page")


class TestAdminPageDetailWithStreamField(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()

        self.homepage = Page.objects.get(url_path="/home/")

    def make_stream_page(self, body):
        stream_page = StreamPage(title="stream page", slug="stream-page", body=body)
        return self.homepage.add_child(instance=stream_page)

    def test_can_fetch_streamfield_content(self):
        stream_page = self.make_stream_page('[{"type": "text", "value": "foo"}]')

        response_url = reverse("wagtailadmin_api:pages:detail", args=(stream_page.id,))
        response = self.client.get(response_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["content-type"], "application/json")

        content = json.loads(response.content.decode("utf-8"))

        self.assertIn("id", content)
        self.assertEqual(content["id"], stream_page.id)
        self.assertIn("body", content)
        self.assertEqual(len(content["body"]), 1)
        self.assertEqual(content["body"][0]["type"], "text")
        self.assertEqual(content["body"][0]["value"], "foo")
        self.assertTrue(content["body"][0]["id"])

    def test_image_block(self):
        stream_page = self.make_stream_page('[{"type": "image", "value": 1}]')

        response_url = reverse("wagtailadmin_api:pages:detail", args=(stream_page.id,))
        response = self.client.get(response_url)
        content = json.loads(response.content.decode("utf-8"))

        # ForeignKeys in a StreamField shouldn't be translated into dictionary representation
        self.assertEqual(content["body"][0]["type"], "image")
        self.assertEqual(content["body"][0]["value"], 1)


class TestCustomAdminDisplayTitle(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()

        self.event_page = Page.objects.get(url_path="/home/events/saint-patrick/")

    def test_custom_admin_display_title_shown_on_detail_page(self):
        api_url = reverse("wagtailadmin_api:pages:detail", args=(self.event_page.id,))
        response = self.client.get(api_url)
        content = json.loads(response.content.decode("utf-8"))

        self.assertEqual(content["title"], "Saint Patrick")
        self.assertEqual(content["admin_display_title"], "Saint Patrick (single event)")

    def test_custom_admin_display_title_shown_on_listing(self):
        api_url = reverse("wagtailadmin_api:pages:listing")
        response = self.client.get(api_url)
        content = json.loads(response.content.decode("utf-8"))

        matching_items = [
            item for item in content["items"] if item["id"] == self.event_page.id
        ]
        self.assertEqual(1, len(matching_items))
        self.assertEqual(matching_items[0]["title"], "Saint Patrick")
        self.assertEqual(
            matching_items[0]["admin_display_title"], "Saint Patrick (single event)"
        )


class TestCopyPageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id, data):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "copy"]), data
        )

    def test_copy_page(self):
        response = self.get_response(3, {})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.title, "Events")
        self.assertEqual(new_page.slug, "events-1")
        self.assertTrue(new_page.live)
        self.assertFalse(new_page.get_children().exists())

    def test_copy_page_change_title(self):
        response = self.get_response(3, {"title": "New title"})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.title, "New title")
        self.assertEqual(new_page.slug, "events-1")

    def test_copy_page_change_slug(self):
        response = self.get_response(3, {"slug": "new-slug"})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.slug, "new-slug")

    def test_copy_page_with_exclude_fields_in_copy(self):
        response = self.get_response(21, {})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        original_page = PageWithExcludedCopyField.objects.get(pk=21)
        new_page = PageWithExcludedCopyField.objects.get(id=content["id"])
        self.assertEqual(new_page.content, original_page.content)
        self.assertNotEqual(new_page.special_field, original_page.special_field)
        self.assertEqual(
            new_page.special_field, new_page._meta.get_field("special_field").default
        )

    def test_copy_page_destination(self):
        response = self.get_response(3, {"destination_page_id": 3})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.title, "Events")
        self.assertTrue(new_page.live)
        self.assertFalse(new_page.get_children().exists())

    def test_copy_page_recursive(self):
        response = self.get_response(
            3,
            {
                "recursive": True,
            },
        )

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.title, "Events")
        self.assertTrue(new_page.get_children().exists())

    def test_copy_page_in_draft(self):
        response = self.get_response(
            3,
            {
                "keep_live": False,
            },
        )

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_page = Page.objects.get(id=content["id"])
        self.assertEqual(new_page.title, "Events")
        self.assertFalse(new_page.live)

    # Check errors

    def test_without_publish_permissions_at_destination_with_keep_live_false(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.user.save()

        response = self.get_response(
            3,
            {
                "destination_page_id": 1,
                "keep_live": False,
            },
        )

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_recursively_copy_into_self(self):
        response = self.get_response(
            3,
            {
                "destination_page_id": 3,
                "recursive": True,
            },
        )

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content,
            {"message": "You cannot copy a tree branch recursively into itself"},
        )

    def test_without_create_permissions_at_destination(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get_response(
            3,
            {
                "destination_page_id": 2,
            },
        )

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_without_publish_permissions_at_destination_with_keep_live(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.user.save()

        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Editors"), page_id=2, permission_type="add"
        )

        response = self.get_response(
            3,
            {
                "destination_page_id": 2,
            },
        )

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_respects_page_creation_rules(self):
        # Only one homepage may exist
        response = self.get_response(2, {})

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_copy_page_slug_in_use(self):
        response = self.get_response(
            3,
            {
                "slug": "events",
            },
        )

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content,
            {
                "slug": [
                    "The slug 'events' is already in use within the parent page at '/'"
                ]
            },
        )


class TestConvertAliasPageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()

        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!", slug="hello-world", content="hello"
        )
        self.root_page.add_child(instance=self.child_page)

        # Add alias page
        self.alias_page = self.child_page.create_alias(update_slug="alias-page")

    def get_response(self, page_id):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "convert_alias"])
        )

    def test_convert_alias(self):
        response = self.get_response(self.alias_page.id)
        self.assertEqual(response.status_code, 200)

        # Check the page was converted
        self.alias_page.refresh_from_db()
        self.assertIsNone(self.alias_page.alias_of)

        # Check that a revision was created
        revision = self.alias_page.revisions.get()
        self.assertEqual(revision.user, self.user)
        self.assertEqual(self.alias_page.live_revision, revision)

        # Check audit log
        log = PageLogEntry.objects.get(action="wagtail.convert_alias")
        self.assertFalse(log.content_changed)
        self.assertEqual(
            log.data,
            {
                "page": {
                    "id": self.alias_page.id,
                    "title": self.alias_page.get_admin_display_title(),
                }
            },
        )
        self.assertEqual(log.page, self.alias_page.page_ptr)
        self.assertEqual(log.revision, revision)
        self.assertEqual(log.user, self.user)

    def test_convert_alias_not_alias(self):
        response = self.get_response(self.child_page.id)
        self.assertEqual(response.status_code, 400)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"message": "Page must be an alias to be converted."})

    def test_convert_alias_bad_permission(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get_response(self.alias_page.id)
        self.assertEqual(response.status_code, 403)


class TestDeletePageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "delete"])
        )

    def test_delete_page(self):
        response = self.get_response(4)

        # Page is deleted
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Page.objects.filter(id=4).exists())

    def test_delete_page_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # delete
        response = self.get_response(4)

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

        # Page is still there
        self.assertTrue(Page.objects.filter(id=4).exists())


class TestPublishPageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "publish"])
        )

    def test_publish_page(self):
        unpublished_page = Page.objects.get(slug="tentative-unpublished-event")
        self.assertIsNone(unpublished_page.first_published_at)
        self.assertEqual(
            unpublished_page.first_published_at, unpublished_page.last_published_at
        )
        self.assertIs(unpublished_page.live, False)

        response = self.get_response(unpublished_page.id)
        self.assertEqual(response.status_code, 200)

        unpublished_page.refresh_from_db()
        self.assertIsNotNone(unpublished_page.first_published_at)
        self.assertEqual(
            unpublished_page.first_published_at, unpublished_page.last_published_at
        )
        self.assertIs(unpublished_page.live, True)

    def test_publish_insufficient_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.groups.add(Group.objects.get(name="Editors"))
        self.user.save()

        response = self.get_response(4)

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_publish_alias_page(self):
        home = Page.objects.get(slug="home")
        alias_page = home.create_alias(update_slug="new-home-page")

        response = self.get_response(alias_page.id)

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content,
            {
                "message": (
                    "page.save_revision() was called on an alias page. "
                    "Revisions are not required for alias pages as they are an exact copy of another page."
                )
            },
        )


class TestUnpublishPageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id, data):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "unpublish"]), data
        )

    def test_unpublish_page(self):
        self.assertTrue(Page.objects.get(id=3).live)

        response = self.get_response(3, {})
        self.assertEqual(response.status_code, 200)

        # Check that the page was unpublished
        self.assertFalse(Page.objects.get(id=3).live)

    def test_unpublish_page_include_descendants(self):
        page = Page.objects.get(slug="home")
        # Check that the page has live descendants that aren't locked.
        self.assertTrue(page.get_descendants().live().filter(locked=False).exists())

        response = self.get_response(page.id, {"recursive": True})
        self.assertEqual(response.status_code, 200)

        # Check that the page is unpublished
        page.refresh_from_db()
        self.assertFalse(page.live)

        # Check that the descendant pages that weren't locked are unpublished as well
        descendant_pages = page.get_descendants().filter(locked=False)
        self.assertTrue(descendant_pages.exists())
        for descendant_page in descendant_pages:
            self.assertFalse(descendant_page.live)

    def test_unpublish_page_without_including_descendants(self):
        page = Page.objects.get(slug="secret-plans")
        # Check that the page has live descendants that aren't locked.
        self.assertTrue(page.get_descendants().live().filter(locked=False).exists())

        response = self.get_response(page.id, {"recursive": False})
        self.assertEqual(response.status_code, 200)

        # Check that the page is unpublished
        page.refresh_from_db()
        self.assertFalse(page.live)

        # Check that the descendant pages that weren't locked aren't unpublished.
        self.assertTrue(page.get_descendants().live().filter(locked=False).exists())

    def test_unpublish_invalid_page_id(self):
        response = self.get_response(12345, {})
        self.assertEqual(response.status_code, 404)

    def test_unpublish_page_insufficient_permission(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get_response(3, {})

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )


class TestMovePageAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id, data):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "move"]), data
        )

    def test_move_page(self):
        response = self.get_response(4, {"destination_page_id": 3})
        self.assertEqual(response.status_code, 200)

    def test_move_page_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        # Move
        response = self.get_response(4, {"destination_page_id": 3})
        self.assertEqual(response.status_code, 403)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_move_page_without_destination_page_id(self):
        response = self.get_response(4, {})
        self.assertEqual(response.status_code, 400)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"destination_page_id": ["This field is required."]})


class TestCopyForTranslationAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def get_response(self, page_id, data):
        return self.client.post(
            reverse(
                "wagtailadmin_api:pages:action", args=[page_id, "copy_for_translation"]
            ),
            data,
        )

    def setUp(self):
        super().setUp()
        self.en_homepage = Page.objects.get(url_path="/home/").specific
        self.en_eventindex = EventIndex.objects.get(url_path="/home/events/")
        self.en_eventpage = EventPage.objects.get(url_path="/home/events/christmas/")
        self.root_page = self.en_homepage.get_parent()
        self.fr_locale = Locale.objects.create(language_code="fr")

    def test_copy_homepage_for_translation(self):
        response = self.get_response(self.en_homepage.id, {"locale": "fr"})

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        fr_homepage = Page.objects.get(id=content["id"])

        self.assertNotEqual(self.en_homepage.id, fr_homepage.id)
        self.assertEqual(fr_homepage.locale, self.fr_locale)
        self.assertEqual(fr_homepage.translation_key, self.en_homepage.translation_key)

        # At the top level, the language code should be appended to the slug
        self.assertEqual(fr_homepage.slug, "home-fr")

        # Translation must be in draft
        self.assertFalse(fr_homepage.live)
        self.assertTrue(fr_homepage.has_unpublished_changes)

    def test_copy_childpage_without_parent(self):
        response = self.get_response(self.en_eventindex.id, {"locale": "fr"})

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"message": "Parent page is not translated."})

    def test_copy_childpage_with_copy_parents(self):
        response = self.get_response(
            self.en_eventindex.id, {"locale": "fr", "copy_parents": True}
        )
        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        fr_eventindex = Page.objects.get(id=content["id"])

        self.assertNotEqual(self.en_eventindex.id, fr_eventindex.id)
        self.assertEqual(fr_eventindex.locale, self.fr_locale)
        self.assertEqual(
            fr_eventindex.translation_key, self.en_eventindex.translation_key
        )
        self.assertEqual(self.en_eventindex.slug, fr_eventindex.slug)

        # This should create the homepage as well
        fr_homepage = fr_eventindex.get_parent()

        self.assertNotEqual(self.en_homepage.id, fr_homepage.id)
        self.assertEqual(fr_homepage.locale, self.fr_locale)
        self.assertEqual(fr_homepage.translation_key, self.en_homepage.translation_key)
        self.assertEqual(fr_homepage.slug, "home-fr")

    def test_copy_for_translation_no_locale(self):
        response = self.get_response(self.en_homepage.id, {})

        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"locale": ["This field is required."]})

    def test_copy_for_translation_unknown_locale(self):
        response = self.get_response(self.en_homepage.id, {"locale": "de"})

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"message": "No Locale matches the given query."})


class TestCreatePageAliasAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()
        self.events_index = EventIndex.objects.get(url_path="/home/events/")
        self.about_us = SimplePage.objects.get(url_path="/home/about-us/")

    def get_response(self, page_id, data):
        return self.client.post(
            reverse("wagtailadmin_api:pages:action", args=[page_id, "create_alias"]),
            data,
        )

    def test_create_alias(self):
        # Set a different draft title, aliases are not supposed to
        # have a different draft_title because they don't have revisions.
        # This should be corrected when copying
        self.about_us.draft_title = "Draft title"
        self.about_us.save(update_fields=["draft_title"])

        response = self.get_response(
            self.about_us.id, data={"update_slug": "new-about-us"}
        )

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_about_us = Page.objects.get(id=content["id"])

        # Check that new_about_us is correct
        self.assertIsInstance(new_about_us.specific, SimplePage)
        self.assertEqual(new_about_us.slug, "new-about-us")
        # Draft title should be changed to match the live title
        self.assertEqual(new_about_us.draft_title, "About us")

        # Check that new_about_us is a different page
        self.assertNotEqual(self.about_us.id, new_about_us.id)

        # Check that the url path was updated
        self.assertEqual(new_about_us.url_path, "/home/new-about-us/")

        # Check that the alias_of field was filled in
        self.assertEqual(new_about_us.alias_of.specific, self.about_us)

    def test_create_alias_recursive(self):
        response = self.get_response(
            self.events_index.id,
            data={"recursive": True, "update_slug": "new-events-index"},
        )

        self.assertEqual(response.status_code, 201)
        content = json.loads(response.content.decode("utf-8"))

        new_events_index = Page.objects.get(id=content["id"])

        # Get christmas event
        old_christmas_event = (
            self.events_index.get_children().filter(slug="christmas").first()
        )
        new_christmas_event = (
            new_events_index.get_children().filter(slug="christmas").first()
        )

        # Check that the event exists in both places
        self.assertIsNotNone(new_christmas_event, "Child pages weren't copied")
        self.assertIsNotNone(
            old_christmas_event, "Child pages were removed from original page"
        )

        # Check that the url path was updated
        self.assertEqual(
            new_christmas_event.url_path, "/home/new-events-index/christmas/"
        )

        # Check that the children were also created as aliases
        self.assertEqual(new_christmas_event.alias_of, old_christmas_event)

    def test_create_alias_doesnt_copy_recursively_to_the_same_tree(self):
        response = self.get_response(
            self.events_index.id,
            data={"recursive": True, "destination_page_id": self.events_index.id},
        )
        self.assertEqual(response.status_code, 400)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content,
            {"message": "You cannot copy a tree branch recursively into itself"},
        )

    def test_create_alias_without_publish_permissions(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get_response(
            self.events_index.id,
            data={"recursive": True, "update_slug": "new-events-index"},
        )
        self.assertEqual(response.status_code, 403)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )


class TestRevertToPageRevisionAction(AdminAPITestCase, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        super().setUp()

        self.events_page = Page.objects.get(id=3)

        # Create revision to revert back to
        self.first_revision = self.events_page.specific.save_revision()

        # Change page title
        self.events_page.title = "Evenements"
        self.events_page.specific.save_revision().publish()

    def get_response(self, page_id, data):
        return self.client.post(
            reverse(
                "wagtailadmin_api:pages:action",
                args=[page_id, "revert_to_page_revision"],
            ),
            data,
        )

    def test_revert_to_page_revision(self):
        self.assertEqual(self.events_page.title, "Evenements")

        response = self.get_response(
            self.events_page.id, {"revision_id": self.first_revision.id}
        )
        self.assertEqual(response.status_code, 200)

        self.events_page.specific.get_latest_revision().publish()
        self.events_page.refresh_from_db()
        self.assertEqual(self.events_page.title, "Events")

    def test_revert_to_page_revision_bad_permissions(self):
        # Remove privileges from user
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        response = self.get_response(
            self.events_page.id, {"revision_id": self.first_revision.id}
        )
        self.assertEqual(response.status_code, 403)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to perform this action."}
        )

    def test_revert_to_page_revision_without_revision_id(self):
        response = self.get_response(self.events_page.id, {})
        self.assertEqual(response.status_code, 400)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"revision_id": ["This field is required."]})

    def test_revert_to_page_revision_bad_revision_id(self):
        self.assertEqual(self.events_page.title, "Evenements")

        response = self.get_response(self.events_page.id, {"revision_id": 999})
        self.assertEqual(response.status_code, 404)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"message": "No Revision matches the given query."})


# Overwrite imported test cases do Django doesn't run them
TestPageDetail = None
TestPageListing = None
