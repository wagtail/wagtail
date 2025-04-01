import collections
import json
from io import StringIO
from unittest import mock

from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from wagtail.api.v2 import signal_handlers
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.models import Locale, Page, Site
from wagtail.models.view_restrictions import BaseViewRestriction
from wagtail.test.demosite import models
from wagtail.test.testapp.models import StreamPage
from wagtail.test.utils import WagtailTestUtils


def get_total_page_count():
    return (
        Page.objects.descendant_of(
            Site.objects.get(is_default_site=True).root_page, inclusive=True
        )
        .live()
        .public()
        .count()
    )


class Test10411APIViewSet(PagesAPIViewSet):
    meta_fields = []


class TestPageListing(WagtailTestUtils, TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v2:pages:listing"), params)

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

        # Check that each page has a meta section with type, detail_url, html_url, slug and first_published_at attributes
        for page in content["items"]:
            self.assertIn("meta", page)
            self.assertIsInstance(page["meta"], dict)
            self.assertEqual(
                set(page["meta"].keys()),
                {"type", "detail_url", "html_url", "slug", "first_published_at"},
            )

    def test_unpublished_pages_dont_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogEntryPage.objects.get(id=16)
        page.unpublish()

        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(content["meta"]["total_count"], total_count - 1)

    def test_private_pages_dont_appear_in_list(self):
        total_count = get_total_page_count()

        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(
            restriction_type=BaseViewRestriction.PASSWORD, password="test"
        )

        new_total_count = get_total_page_count()
        self.assertNotEqual(total_count, new_total_count)

        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(content["meta"]["total_count"], new_total_count)

    def test_private_pages_with_user_login(self):
        client = APIClient()
        user = self.create_user(username="alice", password="password")
        old_total_count = get_total_page_count()
        page = models.BlogIndexPage.objects.get(id=5)
        page.view_restrictions.create(restriction_type="login")
        # authenticate user
        client.force_authenticate(user)
        # getting number of pages after authenticating user
        response = client.get(reverse("wagtailapi_v2:pages:listing"))
        new_total_count = json.loads(response.content.decode("UTF-8"))["meta"][
            "total_count"
        ]
        self.assertEqual(new_total_count, old_total_count)

    def test_private_pages_with_user_groups(self):
        client = APIClient()
        user = self.create_user(username="alice", password="password")
        old_total_count = get_total_page_count()
        page = models.BlogIndexPage.objects.get(id=5)
        editors_group = Group.objects.get(name="Editors")
        page_restriction_instance = page.view_restrictions.create(
            restriction_type="groups"
        )
        page_restriction_instance.groups.add(editors_group)
        # add self.user to editors group and authenticate user
        user.groups.add(editors_group)
        client.force_authenticate(user)
        # getting number of pages after authenticating user
        response = client.get(reverse("wagtailapi_v2:pages:listing"))
        new_total_count = json.loads(response.content.decode("UTF-8"))["meta"][
            "total_count"
        ]
        self.assertEqual(new_total_count, old_total_count)

    def test_page_listing_with_missing_page_model(self):
        # Create a ContentType that doesn't correspond to a real model
        missing_page_content_type = ContentType.objects.create(
            app_label="tests", model="missingpage"
        )

        # Turn a BlogEntryPage into this content_type
        models.BlogEntryPage.objects.filter(id=16).order_by().update(
            content_type=missing_page_content_type
        )

        # get page listing with missing model
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    # TYPE FILTER

    def test_type_filter_items_are_all_blog_entries(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(page["meta"]["type"], "demosite.BlogEntryPage")

            # No specific fields available by default
            self.assertEqual(set(page.keys()), {"id", "meta", "title"})

    def test_type_filter_total_count(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        # Total count must be reduced as this filters the results
        self.assertEqual(content["meta"]["total_count"], 3)

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
            self.assertEqual(set(page.keys()), {"id", "meta", "title"})

        self.assertTrue(blog_page_seen, msg="No blog pages were found in the items")
        self.assertTrue(event_page_seen, msg="No event pages were found in the items")

    def test_non_existent_type_gives_error(self):
        response = self.get_response(type="demosite.IDontExist")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "type doesn't exist"})

    def test_non_page_type_gives_error(self):
        response = self.get_response(type="auth.User")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "type doesn't exist"})

    # LOCALE FILTER

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_locale_filter(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(locale="fr")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], french_homepage.id)

    # TRANSLATION OF FILTER

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_translation_of_filter(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(translation_of=homepage.id)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], french_homepage.id)

    # FIELDS

    def test_fields_default(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta", "title"})
            self.assertEqual(
                set(page["meta"].keys()),
                {"type", "detail_url", "html_url", "slug", "first_published_at"},
            )

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_fields_default_with_i18n_enabled(self):
        # 'locale' should be added to the default set of fields when i18n is enabled
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertIn("locale", set(page["meta"].keys()))

    def test_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title,date,feed_image"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page.keys()), {"id", "meta", "title", "date", "feed_image"}
            )

    def test_remove_fields(self):
        response = self.get_response(fields="-title")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta"})

    def test_remove_meta_fields(self):
        response = self.get_response(fields="-html_url")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta", "title"})
            self.assertEqual(
                set(page["meta"].keys()),
                {"type", "detail_url", "slug", "first_published_at"},
            )

    def test_remove_all_meta_fields(self):
        response = self.get_response(
            fields="-type,-detail_url,-slug,-first_published_at,-html_url"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "title"})

    def test_remove_id_field(self):
        response = self.get_response(fields="-id")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"meta", "title"})

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
                    "alias_of",
                    "seo_title",
                    "slug",
                    "html_url",
                    "search_description",
                    "locale",
                },
            )

    def test_all_fields_then_remove_something(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="*,-title,-date,-seo_title"
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
                    "alias_of",
                    "slug",
                    "html_url",
                    "search_description",
                    "locale",
                },
            )

    def test_remove_all_fields(self):
        response = self.get_response(type="demosite.BlogEntryPage", fields="_,id,type")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta"})
            self.assertEqual(set(page["meta"].keys()), {"type"})

    def test_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(width,height)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page["feed_image"].keys()),
                {"id", "meta", "title", "width", "height"},
            )

    def test_remove_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(-title)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page["feed_image"].keys()), {"id", "meta"})

    def test_all_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(*)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(
                set(page["feed_image"].keys()),
                {"id", "meta", "title", "width", "height"},
            )

    def test_remove_all_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(_,id)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page["feed_image"].keys()), {"id"})

    def test_nested_nested_fields(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="carousel_items(image(width,height))"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            for carousel_item in page["carousel_items"]:
                # Note: inline objects default to displaying all fields
                self.assertEqual(
                    set(carousel_item.keys()),
                    {"id", "meta", "image", "embed_url", "caption", "link"},
                )
                self.assertEqual(
                    set(carousel_item["image"].keys()),
                    {"id", "meta", "title", "width", "height"},
                )

    def test_fields_child_relation(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title,related_links"
        )
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta", "title", "related_links"})
            self.assertIsInstance(page["related_links"], list)

    def test_fields_foreign_key(self):
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
                    "http://localhost/api/main/images/%d/" % feed_image["id"],
                )

    def test_fields_tags(self):
        response = self.get_response(type="demosite.BlogEntryPage", fields="tags")
        content = json.loads(response.content.decode("UTF-8"))

        for page in content["items"]:
            self.assertEqual(set(page.keys()), {"id", "meta", "tags", "title"})
            self.assertIsInstance(page["tags"], list)

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
            "date",
            "feed_image",
            "related_links",
        ]
        self.assertEqual(list(content["items"][0].keys()), field_order)

    def test_star_in_wrong_position_gives_error(self):
        response = self.get_response(fields="title,*")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "fields error: '*' must be in the first position"}
        )

    def test_unknown_nested_fields_give_error(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="feed_image(123,title,abc)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_parent_field_gives_error(self):
        # parent field isn't allowed in listings
        response = self.get_response(fields="parent")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: parent"})

    def test_fields_without_type_gives_error(self):
        response = self.get_response(fields="title,related_links")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: related_links"})

    def test_fields_which_are_not_in_api_fields_gives_error(self):
        response = self.get_response(fields="path")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: path"})

    def test_fields_unknown_field_gives_error(self):
        response = self.get_response(fields="123,title,abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_fields_remove_unknown_field_gives_error(self):
        response = self.get_response(fields="-123,-title,-abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_nested_fields_on_non_relational_field_gives_error(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", fields="title(foo,bar)"
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "'title' does not support nested fields"})

    # FILTERING

    def test_filtering_exact_filter(self):
        response = self.get_response(title="Home page")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2])

    def test_filtering_exact_filter_on_specific_field(self):
        response = self.get_response(type="demosite.BlogEntryPage", date="2013-12-02")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_on_id(self):
        response = self.get_response(id=16)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_on_foreign_key(self):
        response = self.get_response(type="demosite.contactpage", feed_image=7)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [12])

    def test_filtering_on_boolean(self):
        response = self.get_response(show_in_menus="false")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [8, 9, 16, 18, 19, 17])

    def test_filtering_doesnt_work_on_specific_fields_without_type(self):
        response = self.get_response(date="2013-12-02")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "query parameter is not an operation or a recognised field: date"
            },
        )

    def test_filtering_tags(self):
        response = self.get_response(type="demosite.BlogEntryPage", tags="wagtail")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18])

    def test_filtering_multiple_tags(self):
        response = self.get_response(type="demosite.BlogEntryPage", tags="wagtail,bird")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16])

    def test_filtering_unknown_field_gives_error(self):
        response = self.get_response(not_a_field="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "query parameter is not an operation or a recognised field: not_a_field"
            },
        )

    def test_filtering_id_int_validation(self):
        response = self.get_response(id="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "field filter error. 'abc' is not a valid value for id (invalid literal for int() with base 10: 'abc')"
            },
        )

    def test_filtering_foreign_key_int_validation(self):
        response = self.get_response(type="demosite.contactpage", feed_image="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content["message"][:61],
            "field filter error. 'abc' is not a valid value for feed_image",
        )

    def test_filtering_boolean_validation(self):
        response = self.get_response(show_in_menus="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "field filter error. 'abc' is not a valid value for show_in_menus (expected 'true' or 'false', got 'abc')"
            },
        )

    def test_slug_field_containing_null_bytes_gives_error(self):
        response = self.get_response(slug="\0")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {"message": "field filter error. null characters are not allowed for slug"},
        )

    # CHILD OF FILTER

    def test_child_of_filter(self):
        response = self.get_response(child_of=5)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_child_of_root(self):
        # "root" gets children of the homepage of the current site
        response = self.get_response(child_of="root")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [4, 5, 6, 20, 12])

    def test_child_of_with_type(self):
        response = self.get_response(type="demosite.EventPage", child_of=5)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [])

    def test_child_of_unknown_page_gives_error(self):
        response = self.get_response(child_of=1000)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "parent page doesn't exist"})

    def test_child_of_not_integer_gives_error(self):
        response = self.get_response(child_of="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "child_of must be a positive integer"})

    def test_child_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(child_of=1)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "parent page doesn't exist"})

    # ANCESTOR OF FILTER

    def test_ancestor_of_filter(self):
        response = self.get_response(ancestor_of=10)
        content = response.json()

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [2, 6])

    def test_ancestor_of_with_type(self):
        response = self.get_response(type="demosite.eventindexpage", ancestor_of=8)
        content = response.json()

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [4])

    def test_ancestor_of_unknown_page_gives_error(self):
        response = self.get_response(ancestor_of=1000)
        content = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "descendant page doesn't exist"})

    def test_ancestor_of_not_integer_gives_error(self):
        response = self.get_response(ancestor_of="abc")
        content = response.json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "ancestor_of must be a positive integer"})

    def test_ancestor_of_home_page_ignores_root(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(ancestor_of=2)
        content = response.json()

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [])

    # DESCENDANT OF FILTER

    def test_descendant_of_filter(self):
        response = self.get_response(descendant_of=6)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [10, 15, 17, 21, 22, 23])

    def test_descendant_of_root(self):
        # "root" gets descendants of the homepage of the current site
        # Basically returns every page except the homepage
        response = self.get_response(descendant_of="root")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12],
        )

    def test_descendant_of_with_type(self):
        response = self.get_response(type="demosite.eventindexpage", descendant_of=2)
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [4])

    def test_descendant_of_unknown_page_gives_error(self):
        response = self.get_response(descendant_of=1000)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "ancestor page doesn't exist"})

    def test_descendant_of_not_integer_gives_error(self):
        response = self.get_response(descendant_of="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "descendant_of must be a positive integer"}
        )

    def test_descendant_of_page_thats_not_in_same_site_gives_error(self):
        # Root page is not in any site, so pretend it doesn't exist
        response = self.get_response(descendant_of=1)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "ancestor page doesn't exist"})

    def test_descendant_of_when_filtering_by_child_of_gives_error(self):
        response = self.get_response(descendant_of=6, child_of=5)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {"message": "filtering by descendant_of with child_of is not supported"},
        )

    # SITE FILTER

    def test_site_filter_same_hostname_returns_error(self):
        response = self.get_response(site="localhost")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(
            content,
            {
                "message": "Your query returned multiple sites. Try adding a port number to your site filter."
            },
        )

    def test_site_filter(self):
        response = self.get_response(site="localhost:8001")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [24, 25])

    # ORDERING

    def test_ordering_default(self):
        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [2, 4, 8, 9, 5, 16, 18, 19, 6, 10, 15, 17, 21, 22, 23, 20, 13, 14, 12],
        )

    def test_ordering_by_title(self):
        response = self.get_response(order="title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [21, 22, 19, 23, 5, 16, 18, 12, 14, 8, 9, 4, 2, 13, 20, 17, 6, 10, 15],
        )

    def test_ordering_by_title_backwards(self):
        response = self.get_response(order="-title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(
            page_id_list,
            [15, 10, 6, 17, 20, 13, 2, 4, 9, 8, 14, 12, 18, 16, 5, 23, 19, 22, 21],
        )

    def test_ordering_by_random(self):
        response_1 = self.get_response(order="random")
        content_1 = json.loads(response_1.content.decode("UTF-8"))
        page_id_list_1 = self.get_page_id_list(content_1)

        response_2 = self.get_response(order="random")
        content_2 = json.loads(response_2.content.decode("UTF-8"))
        page_id_list_2 = self.get_page_id_list(content_2)

        self.assertNotEqual(page_id_list_1, page_id_list_2)

    def test_ordering_by_random_backwards_gives_error(self):
        response = self.get_response(order="-random")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "cannot order by 'random' (unknown field)"}
        )

    def test_ordering_by_random_with_offset_gives_error(self):
        response = self.get_response(order="random", offset=10)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "random ordering with offset is not supported"}
        )

    def test_ordering_default_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_ordering_by_title_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", order="title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [19, 16, 18])

    def test_ordering_by_specific_field_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", order="date")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [16, 18, 19])

    def test_ordering_by_unknown_field_gives_error(self):
        response = self.get_response(order="not_a_field")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "cannot order by 'not_a_field' (unknown field)"}
        )

    def test_random_ordering_with_unknown_field_gives_error(self):
        response = self.get_response(order=["random,id"])
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "random ordering cannot be combined with other fields"}
        )

    def test_ordering_by_id_and_slug(self):
        response = self.get_response(order=["id,slug"])
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        expected_order = [
            2,
            4,
            5,
            6,
            8,
            9,
            10,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
        ]
        self.assertEqual(page_id_list[:15], expected_order[:15])

    def test_ordering_by_title_and_id_backwards(self):
        response = self.get_response(order=["title,-id"])
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)
        expected_order = [
            15,
            10,
            6,
            17,
            20,
            13,
            2,
            4,
            9,
            8,
            14,
            12,
            18,
            16,
            5,
            23,
            19,
            22,
            21,
        ]
        self.assertEqual(page_id_list[:5], expected_order[:5])

    # LIMIT

    def test_limit_only_two_items_returned(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(len(content["items"]), 2)

    def test_limit_total_count(self):
        response = self.get_response(limit=2)
        content = json.loads(response.content.decode("UTF-8"))

        # The total count must not be affected by "limit"
        self.assertEqual(content["meta"]["total_count"], get_total_page_count())

    def test_limit_not_integer_gives_error(self):
        response = self.get_response(limit="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "limit must be a positive integer"})

    def test_limit_too_high_gives_error(self):
        response = self.get_response(limit=1000)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "limit cannot be higher than 20"})

    @override_settings(WAGTAILAPI_LIMIT_MAX=None)
    def test_limit_max_none_gives_no_errors(self):
        response = self.get_response(limit=1000000)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(content["items"]), get_total_page_count())

    @override_settings(WAGTAILAPI_LIMIT_MAX=10)
    def test_limit_maximum_can_be_changed(self):
        response = self.get_response(limit=20)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "limit cannot be higher than 10"})

    @override_settings(WAGTAILAPI_LIMIT_MAX=2)
    def test_limit_default_changes_with_max(self):
        # The default limit is 20. If WAGTAILAPI_LIMIT_MAX is less than that,
        # the default should change accordingly.
        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(len(content["items"]), 2)

    # OFFSET

    def test_offset_5_usually_appears_5th_in_list(self):
        response = self.get_response()
        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list.index(5), 4)

    def test_offset_5_moves_after_offset(self):
        response = self.get_response(offset=4)
        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list.index(5), 0)

    def test_offset_total_count(self):
        response = self.get_response(offset=10)
        content = json.loads(response.content.decode("UTF-8"))

        # The total count must not be affected by "offset"
        self.assertEqual(content["meta"]["total_count"], get_total_page_count())

    def test_offset_not_integer_gives_error(self):
        response = self.get_response(offset="abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "offset must be a positive integer"})

    # REGRESSION TESTS

    def test_issue_3967(self):
        # The API crashed whenever the listing view was called without a site configured
        Site.objects.all().delete()
        response = self.get_response()
        self.assertEqual(response.status_code, 200)

    def test_issue_10411(self):
        # Bug with removing meta fields from API
        response = self.client.get(reverse("wagtailapi_v2:issue_10411:listing"))
        self.assertEqual(response.status_code, 200)


class TestPageListingSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["demosite.json"]

    def setUp(self):
        super().setUp()
        management.call_command(
            "update_index",
            backend_name="default",
            stdout=StringIO(),
            chunk_size=50,
        )

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v2:pages:listing"), params)

    def get_page_id_list(self, content):
        return [page["id"] for page in content["items"]]

    def get_homepage(self):
        return Page.objects.get(slug="home-page")

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_locale_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()
        events_index = Page.objects.get(url_path="/home-page/events-index/")
        french_events_index = events_index.copy_for_translation(french)
        french_events_index.get_latest_revision().publish()

        response = self.get_response(locale="fr", search="events")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], french_events_index.id)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_translation_of_filter_with_search(self):
        french = Locale.objects.create(language_code="fr")
        homepage = self.get_homepage()
        french_homepage = homepage.copy_for_translation(french)
        french_homepage.get_latest_revision().publish()

        response = self.get_response(translation_of=homepage.id, search="home")
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(len(content["items"]), 1)
        self.assertEqual(content["items"][0]["id"], french_homepage.id)
        response = self.get_response(translation_of=homepage.id, search="gnome")
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(len(content["items"]), 0)

    def test_search_for_blog(self):
        response = self.get_response(search="blog")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        # Check that the items are the blog index and three blog pages
        self.assertEqual(set(page_id_list), {5, 16, 18, 19})

    def test_search_with_type(self):
        response = self.get_response(type="demosite.BlogEntryPage", search="blog")
        content = json.loads(response.content.decode("UTF-8"))
        page_id_list = self.get_page_id_list(content)

        self.assertEqual(set(page_id_list), {16, 18, 19})

    def test_search_with_invalid_type(self):
        # Check that a 400 error is returned when the type doesn't exist
        response = self.get_response(type="demosite.InvalidPageType", search="blog")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "type doesn't exist"})

    def test_search_with_filter(self):
        response = self.get_response(
            title="Another blog post", search="blog", order="title"
        )
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [19])

    def test_search_with_filter_on_non_filterable_field(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", body="foo", search="blog", order="title"
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "cannot filter by 'body' while searching (field is not indexed)"
            },
        )

    def test_search_with_order(self):
        response = self.get_response(search="blog", order="title")
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(page_id_list, [19, 5, 16, 18])

    def test_search_with_order_on_non_filterable_field(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", search="blog", order="body"
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {
                "message": "cannot order by 'body' while searching (field is not indexed)"
            },
        )

    @override_settings(WAGTAILAPI_SEARCH_ENABLED=False)
    def test_search_when_disabled_gives_error(self):
        response = self.get_response(search="blog")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "search is disabled"})

    def test_search_when_filtering_by_tag_gives_error(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", search="blog", tags="wagtail"
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content,
            {"message": "filtering by tag with a search query is not supported"},
        )

    def test_search_operator_and(self):
        response = self.get_response(
            type="demosite.BlogEntryPage",
            search="blog elephants",
            search_operator="and",
        )
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(set(page_id_list), {18})

    def test_search_operator_or(self):
        response = self.get_response(
            type="demosite.BlogEntryPage", search="blog elephants", search_operator="or"
        )
        content = json.loads(response.content.decode("UTF-8"))

        page_id_list = self.get_page_id_list(content)

        self.assertEqual(set(page_id_list), {16, 18, 19})

    def test_empty_searches_work(self):
        response = self.get_response(search="")
        content = json.loads(response.content.decode("UTF-8"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")
        self.assertEqual(content["meta"]["total_count"], 0)


class TestPageDetail(TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, page_id, **params):
        return self.client.get(
            reverse("wagtailapi_v2:pages:detail", args=(page_id,)), params
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
            content["meta"]["detail_url"], "http://localhost/api/main/pages/16/"
        )

        # Check the meta html_url
        self.assertIn("html_url", content["meta"])
        self.assertEqual(
            content["meta"]["html_url"], "http://localhost/blog-index/blog-post/"
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
            "http://localhost/api/main/pages/5/",
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
            "http://localhost/api/main/images/7/",
        )

        # Check that the feed images' thumbnail was serialised properly
        self.assertEqual(
            content["feed_image_thumbnail"],
            {
                # This is OK because it tells us it used ImageRenditionField to generate the output
                "error": "SourceImageIOError"
            },
        )

        # Check that the child relations were serialised properly
        self.assertEqual(content["related_links"], [])
        for carousel_item in content["carousel_items"]:
            self.assertEqual(
                set(carousel_item.keys()),
                {"id", "meta", "embed_url", "link", "caption", "image"},
            )
            self.assertEqual(set(carousel_item["meta"].keys()), {"type"})

    def test_meta_parent_id_doesnt_show_root_page(self):
        # Root page isn't in the site so don't show it if the user is looking at the home page
        response = self.get_response(2)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIsNone(content["meta"]["parent"])

    def test_field_ordering(self):
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
            "body",
            "tags",
            "date",
            "feed_image",
            "feed_image_thumbnail",
            "carousel_items",
            "related_links",
        ]
        self.assertEqual(list(content.keys()), field_order)

        meta_field_order = [
            "type",
            "detail_url",
            "html_url",
            "slug",
            "show_in_menus",
            "seo_title",
            "search_description",
            "first_published_at",
            "alias_of",
            "parent",
        ]
        self.assertEqual(list(content["meta"].keys()), meta_field_order)

    def test_null_foreign_key(self):
        models.BlogEntryPage.objects.filter(id=16).order_by().update(feed_image_id=None)

        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("related_links", content)
        self.assertIsNone(content["feed_image"])

    def test_page_with_missing_page_model(self):
        # Create a ContentType that doesn't correspond to a real model
        missing_page_content_type = ContentType.objects.create(
            app_label="tests", model="missingpage"
        )

        # Turn a BlogEntryPage into this content_type
        models.BlogEntryPage.objects.filter(id=16).order_by().update(
            content_type=missing_page_content_type
        )

        # get missing model page
        response = self.get_response(16)
        self.assertEqual(response.status_code, 200)

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
            "http://localhost/api/main/pages/16/",
        )
        self.assertEqual(
            content["meta"]["alias_of"]["meta"]["html_url"],
            "http://localhost/blog-index/blog-post/",
        )

    # FIELDS

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_default_fields_with_i18n_enabled(self):
        # 'locale' should be added to the default set of fields when i18n is enabled
        response = self.get_response(16)
        page = json.loads(response.content.decode("UTF-8"))

        self.assertIn("locale", set(page["meta"].keys()))

    def test_remove_fields(self):
        response = self.get_response(16, fields="-title")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("id", set(content.keys()))
        self.assertNotIn("title", set(content.keys()))

    def test_remove_meta_fields(self):
        response = self.get_response(16, fields="-html_url")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("detail_url", set(content["meta"].keys()))
        self.assertNotIn("html_url", set(content["meta"].keys()))

    def test_remove_all_meta_fields(self):
        response = self.get_response(
            16,
            fields="-type,-detail_url,-slug,-first_published_at,-alias_of,-html_url,-search_description,-show_in_menus,-parent,-seo_title",
        )
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("id", set(content.keys()))
        self.assertNotIn("meta", set(content.keys()))

    def test_remove_id_field(self):
        response = self.get_response(16, fields="-id")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIn("title", set(content.keys()))
        self.assertNotIn("id", set(content.keys()))

    def test_remove_all_fields(self):
        response = self.get_response(16, fields="_,id,type")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(set(content.keys()), {"id", "meta"})
        self.assertEqual(set(content["meta"].keys()), {"type"})

    def test_nested_fields(self):
        response = self.get_response(16, fields="feed_image(width,height)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(
            set(content["feed_image"].keys()),
            {"id", "meta", "title", "width", "height"},
        )

    def test_remove_nested_fields(self):
        response = self.get_response(16, fields="feed_image(-title)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(set(content["feed_image"].keys()), {"id", "meta"})

    def test_all_nested_fields(self):
        response = self.get_response(16, fields="feed_image(*)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(
            set(content["feed_image"].keys()),
            {"id", "meta", "title", "width", "height"},
        )

    def test_remove_all_nested_fields(self):
        response = self.get_response(16, fields="feed_image(_,id)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(set(content["feed_image"].keys()), {"id"})

    def test_nested_nested_fields(self):
        response = self.get_response(16, fields="carousel_items(image(width,height))")
        content = json.loads(response.content.decode("UTF-8"))

        for carousel_item in content["carousel_items"]:
            # Note: inline objects default to displaying all fields
            self.assertEqual(
                set(carousel_item.keys()),
                {"id", "meta", "image", "embed_url", "caption", "link"},
            )
            self.assertEqual(
                set(carousel_item["image"].keys()),
                {"id", "meta", "title", "width", "height"},
            )

    def test_fields_child_relation_is_list(self):
        response = self.get_response(16)
        content = json.loads(response.content.decode("UTF-8"))

        self.assertIsInstance(content["related_links"], list)

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
            "http://localhost/api/main/images/%d/" % feed_image["id"],
        )

    def test_star_in_wrong_position_gives_error(self):
        response = self.get_response(16, fields="title,*")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            content, {"message": "fields error: '*' must be in the first position"}
        )

    def test_unknown_nested_fields_give_error(self):
        response = self.get_response(16, fields="feed_image(123,title,abc)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_fields_which_are_not_in_api_fields_gives_error(self):
        response = self.get_response(16, fields="path")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: path"})

    def test_fields_unknown_field_gives_error(self):
        response = self.get_response(16, fields="123,title,abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_fields_remove_unknown_field_gives_error(self):
        response = self.get_response(16, fields="-123,-title,-abc")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "unknown fields: 123, abc"})

    def test_nested_fields_on_non_relational_field_gives_error(self):
        response = self.get_response(16, fields="title(foo,bar)")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(content, {"message": "'title' does not support nested fields"})

    def test_form_fields_on_form_page(self):
        """
        Check that adding form_fields will correctly return then in the API response when declared
        """

        home_page = Page.objects.get(slug="home-page")
        form_page = home_page.add_child(instance=models.FormPage(title="Contact us"))

        field_1 = models.FormField.objects.create(
            page=form_page,
            sort_order=1,
            label="email",
            field_type="email",
        )
        field_2 = models.FormField.objects.create(
            page=form_page,
            sort_order=2,
            label="message",
            field_type="multiline",
            required=True,
            help_text="<em>please</em> be polite",
        )

        response = self.get_response(form_page.pk, fields="form_fields")
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(
            content["form_fields"],
            [
                {
                    "id": field_1.pk,
                    "clean_name": "email",
                    "meta": {"type": "demosite.FormField"},
                    "label": "email",
                    "help_text": "",
                    "required": True,
                    "field_type": "email",
                    "choices": "",
                    "default_value": "",
                },
                {
                    "id": field_2.pk,
                    "clean_name": "message",
                    "meta": {"type": "demosite.FormField"},
                    "label": "message",
                    "help_text": "<em>please</em> be polite",
                    "required": True,
                    "field_type": "multiline",
                    "choices": "",
                    "default_value": "",
                },
            ],
        )


class TestPageFind(TestCase):
    fixtures = ["demosite.json"]

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v2:pages:find"), params)

    def test_without_parameters(self):
        response = self.get_response()

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(content, {"message": "not found"})

    def test_find_by_id(self):
        response = self.get_response(id=5)

        self.assertRedirects(
            response,
            "http://localhost" + reverse("wagtailapi_v2:pages:detail", args=[5]),
            fetch_redirect_response=False,
        )

    def test_find_by_id_nonexistent(self):
        response = self.get_response(id=1234)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(content, {"message": "not found"})

    def test_find_by_html_path(self):
        response = self.get_response(html_path="/events-index/event-1/")

        self.assertRedirects(
            response,
            "http://localhost" + reverse("wagtailapi_v2:pages:detail", args=[8]),
            fetch_redirect_response=False,
        )

    def test_find_by_html_path_with_start_and_end_slashes_removed(self):
        response = self.get_response(html_path="events-index/event-1")

        self.assertRedirects(
            response,
            "http://localhost" + reverse("wagtailapi_v2:pages:detail", args=[8]),
            fetch_redirect_response=False,
        )

    def test_find_by_html_path_nonexistent(self):
        response = self.get_response(html_path="/foo")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response["Content-type"], "application/json")

        # Will crash if the JSON is invalid
        content = json.loads(response.content.decode("UTF-8"))

        self.assertEqual(content, {"message": "not found"})


class TestPageDetailWithStreamField(TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.homepage = Page.objects.get(url_path="/home/")

    def make_stream_page(self, body):
        stream_page = StreamPage(title="stream page", slug="stream-page", body=body)
        return self.homepage.add_child(instance=stream_page)

    def test_can_fetch_streamfield_content(self):
        stream_page = self.make_stream_page('[{"type": "text", "value": "foo"}]')

        response_url = reverse("wagtailapi_v2:pages:detail", args=(stream_page.id,))
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

    def test_image_chooser_block(self):
        stream_page = self.make_stream_page('[{"type": "image", "value": 1}]')

        response_url = reverse("wagtailapi_v2:pages:detail", args=(stream_page.id,))
        response = self.client.get(response_url)
        content = json.loads(response.content.decode("utf-8"))

        # ForeignKeys in a StreamField shouldn't be translated into dictionary representation
        self.assertEqual(content["body"][0]["type"], "image")
        self.assertEqual(content["body"][0]["value"], 1)

    def test_image_chooser_block_with_custom_get_api_representation(self):
        stream_page = self.make_stream_page('[{"type": "image", "value": 1}]')

        response_url = "{}?extended=1".format(
            reverse("wagtailapi_v2:pages:detail", args=(stream_page.id,))
        )
        response = self.client.get(response_url)
        content = json.loads(response.content.decode("utf-8"))

        # the custom get_api_representation returns a dict of id and title for the image
        self.assertEqual(content["body"][0]["type"], "image")
        self.assertEqual(
            content["body"][0]["value"], {"id": 1, "title": "A missing image"}
        )

    def test_image_block(self):
        stream_page = self.make_stream_page(
            '[{"type": "image_with_alt", "value": {"image": 1, "alt_text": "Some alt text", "decorative": false}}]'
        )

        response_url = reverse("wagtailapi_v2:pages:detail", args=(stream_page.id,))
        response = self.client.get(response_url)
        content = json.loads(response.content.decode("utf-8"))

        self.assertEqual(content["body"][0]["type"], "image_with_alt")
        self.assertEqual(content["body"][0]["value"]["image"], 1)
        self.assertEqual(content["body"][0]["value"]["alt_text"], "Some alt text")


@override_settings(
    WAGTAILFRONTENDCACHE={
        "varnish": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.HTTPBackend",
            "LOCATION": "http://localhost:8000",
        },
    },
    WAGTAILAPI_BASE_URL="http://api.example.com",
)
@mock.patch("wagtail.contrib.frontend_cache.backends.http.HTTPBackend.purge")
class TestPageCacheInvalidation(TestCase):
    fixtures = ["demosite.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        signal_handlers.register_signal_handlers()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        signal_handlers.unregister_signal_handlers()

    def test_republish_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision().publish()

        purge.assert_any_call("http://api.example.com/api/main/pages/2/")

    def test_unpublish_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).unpublish()

        purge.assert_any_call("http://api.example.com/api/main/pages/2/")

    def test_delete_page_purges(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=16).delete()

        purge.assert_any_call("http://api.example.com/api/main/pages/16/")

    def test_save_draft_doesnt_purge(self, purge):
        with self.captureOnCommitCallbacks(execute=True):
            Page.objects.get(id=2).specific.save_revision()

        purge.assert_not_called()


class TestPageViewSetSubclassing(PagesAPIViewSet):
    model = models.BlogEntryPage

    def test_get_queryset(self):
        self.assertEqual(
            self.get_queryset().model,
            models.BlogEntryPage,
        )
