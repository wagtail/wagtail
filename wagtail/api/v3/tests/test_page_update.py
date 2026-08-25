import json

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import GroupPagePermission
from wagtail.test.demosite.models import (
    BlogEntryPage,
    BlogIndexPage,
    EventPage,
    HomePage,
)
from wagtail.test.testapp.models import StreamPage
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3PageUpdate(TestV3Base, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.root_page = Page.objects.get(depth=1)
        self.user = self.login()

    def patch(self, page, data):
        return self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": page.pk}),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_anonymous_returns_401(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.unauthorize()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_update_page(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "New title")
        # slug wasn't sent, so it must be untouched.
        self.assertEqual(page.slug, "original")

        content = response.json()
        self.assertEqual(content["title"], "New title")
        self.assertEqual(content["meta"]["slug"], "original")

    def test_omitted_field_is_left_untouched(self):
        """
        This is a partial update: a writable field that isn't in the request
        body must keep its existing value, not get cleared to empty/False -
        which is what would happen if it were bound on the form unset.
        """
        page = self.root_page.add_child(
            instance=BlogIndexPage(
                title="Original", slug="original", intro="this is the intro", live=False
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.intro, "this is the intro")

    def test_omitted_non_blank_extra_field_does_not_fail_validation(self):
        """
        EventPage.date_from is a plain, non-blank model field exposed as a
        writable APIField. It's required on create, but omitting it from a
        patch must not be rejected as missing - the patch schema forces
        every such field optional (see patch_generator's force_optional),
        independent of what the create schema requires for the same field.
        """
        page = self.root_page.add_child(
            instance=EventPage(
                title="Event",
                slug="event",
                date_from="2026-01-01",
                audience="public",
                location="Somewhere",
                cost="Free",
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.EventPage"},
                "title": "Event Renamed",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "Event Renamed")
        self.assertEqual(str(page.date_from), "2026-01-01")

    def test_update_page_with_publish_action_publishes_page(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.assertFalse(page.live)
        logs_since = timezone.now()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage", "action": "publish"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.live)
        self.assertEqual(page.title, "New title")
        self.assertIsNotNone(page.live_revision)
        self.assertEqual(page.live_revision, page.latest_revision)
        self.assert_log_actions(
            page,
            ["wagtail.edit", "wagtail.publish"],
            since=logs_since,
        )

    def test_update_live_page_with_publish_action_logs_rename(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        page.save_revision().publish()
        page.refresh_from_db()
        self.assertTrue(page.live)
        logs_since = timezone.now()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage", "action": "publish"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertTrue(page.live)
        self.assertEqual(page.title, "New title")
        self.assertIsNotNone(page.live_revision)
        self.assertEqual(page.live_revision, page.latest_revision)
        self.assert_log_actions(
            page,
            ["wagtail.edit", "wagtail.rename", "wagtail.publish"],
            since=logs_since,
        )

    def test_update_page_with_invalid_action_returns_422(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {
                    "type": "demosite.BlogIndexPage",
                    "action": "not_a_real_action",
                },
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=422)

    def test_update_saves_one_revision_and_logs_edit(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        logs_since = timezone.now()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.revisions.count(), 1)
        self.assert_log_actions(page, ["wagtail.edit"], since=logs_since)

    def test_update_page_with_api_field(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[{"type": "text", "value": "hello world"}],
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [{"type": "text", "value": "updated"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.body[0].value, "updated")
        # title wasn't sent, so it must be untouched.
        self.assertEqual(page.title, "Stream page")

    def test_update_page_without_block_id_regenerates_it(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[{"type": "text", "value": "original"}],
                live=False,
            )
        )
        original_id = page.body[0].id
        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [{"type": "text", "value": "updated"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.body[0].value, "updated")
        self.assertNotEqual(page.body[0].id, original_id)

    def test_update_page_with_block_id_preserves_it(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[{"type": "text", "value": "original"}],
                live=False,
            )
        )
        original_id = page.body[0].id
        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [{"type": "text", "value": "updated", "id": original_id}],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.body[0].value, "updated")
        self.assertEqual(page.body[0].id, original_id)

    def test_update_page_with_streamfield_diffing(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[
                    {"type": "text", "value": "first"},
                    {"type": "text", "value": "second"},
                    {"type": "text", "value": "third"},
                ],
                live=False,
            )
        )
        first_id, second_id, third_id = (block.id for block in page.body)

        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [
                    {"type": "text", "value": "third updated", "id": third_id},
                    {"type": "text", "value": "first updated", "id": first_id},
                    {"type": "text", "value": "new block"},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(len(page.body), 3)
        self.assertEqual(page.body[0].value, "third updated")
        self.assertEqual(page.body[0].id, third_id)
        self.assertEqual(page.body[1].value, "first updated")
        self.assertEqual(page.body[1].id, first_id)
        self.assertEqual(page.body[2].value, "new block")
        self.assertNotIn(page.body[2].id, {first_id, second_id, third_id})

    def test_update_page_with_rich_text_block(self):
        page = self.root_page.add_child(
            instance=StreamPage(
                title="Stream page",
                slug="stream-page",
                body=[{"type": "rich_text", "value": "<p>original</p>"}],
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "tests.StreamPage"},
                "body": [{"type": "rich_text", "value": "<p>updated <b>text</b></p>"}],
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.body[0].block_type, "rich_text")
        self.assertIn("updated <b>text</b>", str(page.body[0].value))

    def test_update_page_with_various_block_types(self):
        original_image = Image.objects.create(
            title="Original image", file=get_test_image_file()
        )
        new_image = Image.objects.create(title="New image", file=get_test_image_file())
        original_table = {
            "data": [["", "Original"], ["Row", "1"]],
            "first_col_is_header": True,
            "first_row_is_table_header": True,
            "mergeCells": [],
            "table_caption": "Original table",
            "table_header_choice": "both",
        }
        updated_table = {
            "data": [["", "Updated"], ["Row", "2"]],
            "first_col_is_header": True,
            "first_row_is_table_header": True,
            "mergeCells": [],
            "table_caption": "Updated table",
            "table_header_choice": "both",
        }
        cases = [
            (
                "product",
                {"name": "Original", "price": "1.00"},
                {"name": "Widget", "price": "9.99"},
                lambda value: (
                    self.assertEqual(value["name"], "Widget"),
                    self.assertEqual(value["price"], "9.99"),
                ),
                lambda value: self.assertEqual(
                    value, {"name": "Widget", "price": "9.99"}
                ),
            ),
            (
                "raw_html",
                "<div>original</div>",
                "<div>updated</div>",
                lambda value: self.assertEqual(str(value), "<div>updated</div>"),
                lambda value: self.assertEqual(value, "<div>updated</div>"),
            ),
            (
                "books",
                [{"type": "title", "value": "Original"}],
                [
                    {"type": "title", "value": "Dune"},
                    {"type": "author", "value": "Frank Herbert"},
                ],
                lambda value: (
                    self.assertEqual(value[0].value, "Dune"),
                    self.assertEqual(value[1].value, "Frank Herbert"),
                ),
                # Each child gets its own server-generated "id" - assert one
                # is present, then compare the rest.
                lambda value: (
                    self.assertTrue(all(item["id"] for item in value)),
                    self.assertEqual(
                        [
                            {k: v for k, v in item.items() if k != "id"}
                            for item in value
                        ],
                        [
                            {"type": "title", "value": "Dune"},
                            {"type": "author", "value": "Frank Herbert"},
                        ],
                    ),
                ),
            ),
            (
                "title_list",
                ["Original"],
                ["First", "Second", "Third"],
                lambda value: self.assertEqual(
                    list(value), ["First", "Second", "Third"]
                ),
                lambda value: self.assertEqual(value, ["First", "Second", "Third"]),
            ),
            (
                "image",
                original_image.pk,
                new_image.pk,
                lambda value: self.assertEqual(value.pk, new_image.pk),
                lambda value: self.assertEqual(value, new_image.pk),
            ),
            (
                "image_with_alt",
                {
                    "image": original_image.pk,
                    "decorative": False,
                    "alt_text": "Original alt",
                },
                {
                    "image": original_image.pk,
                    "decorative": False,
                    "alt_text": "Updated alt",
                },
                lambda value: self.assertEqual(
                    value.contextual_alt_text, "Updated alt"
                ),
                lambda value: self.assertEqual(
                    value,
                    {
                        "image": original_image.pk,
                        "decorative": False,
                        "alt_text": "Updated alt",
                    },
                ),
            ),
            (
                "table",
                original_table,
                updated_table,
                lambda value: self.assertEqual(value, updated_table),
                lambda value: self.assertEqual(value, updated_table),
            ),
        ]
        for (
            block_type,
            original_value,
            updated_value,
            assert_db_value,
            assert_api_value,
        ) in cases:
            with self.subTest(block_type=block_type):
                page = self.root_page.add_child(
                    instance=StreamPage(
                        title="Stream page",
                        slug=f"stream-page-{block_type}",
                        body=[{"type": block_type, "value": original_value}],
                        live=False,
                    )
                )
                response = self.patch(
                    page,
                    {
                        "meta": {"type": "tests.StreamPage"},
                        "body": [{"type": block_type, "value": updated_value}],
                    },
                )
                self.assertEqual(response.status_code, 200)

                page.refresh_from_db()
                self.assertEqual(page.body[0].block_type, block_type)
                assert_db_value(page.body[0].value)

                [block] = response.json()["body"]
                self.assertEqual(block["type"], block_type)
                self.assertTrue(block["id"])
                assert_api_value(block["value"])

    def test_update_page_with_non_writable_api_field_ignores_it(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(
                title="Original",
                slug="original",
                intro="Original intro",
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "intro": "should be ignored",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.intro, "Original intro")

    def test_update_page_with_unknown_field_ignores_it(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "not_a_real_field_at_all": "should be ignored",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_update_page_with_duplicate_slug_returns_422(self):
        self.root_page.add_child(
            instance=BlogIndexPage(title="Existing", slug="existing", live=False)
        )
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "slug": "existing",
            },
        )
        self.assert_problem_response(response, status_code=422)

    def test_update_page_with_child_relations_replaces_them(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-with-children", body="<p>hi</p>", live=False
            )
        )
        # DeferringRelatedManager.create() only stages the child in memory -
        # it isn't written to the database until the parent is saved.
        page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "caption": "New",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        # refresh_from_db() doesn't clear modelcluster's own child-relation
        # cache, so re-fetch the page outright to see the real DB state.
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "New")

    def test_update_page_with_child_relation_id_edits_in_place(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home",
                slug="home-with-matched-child",
                body="<p>hi</p>",
                live=False,
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "id": item.pk,
                        "caption": "Edited",
                        "link_external": "http://example.com/old",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].pk, item.pk)
        self.assertEqual(items[0].caption, "Edited")

    def test_update_of_live_page_does_not_touch_live_rows_until_published(self):
        """
        Updating a live page without publishing must save the changes as a
        new draft revision - matching the admin edit view - without
        touching the live DB rows for the page or its child relations.
        Publishing the resulting revision is what applies the change.
        """
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-live-draft-edit", body="<p>hi</p>", live=True
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        page.save_revision().publish()

        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "title": "New Draft Title",
                "carousel_items": [
                    {
                        "caption": "New Draft Item",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)

        page = HomePage.objects.get(pk=page.pk)
        self.assertTrue(page.live)
        self.assertEqual(page.title, "Home")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].pk, item.pk)
        self.assertEqual(items[0].caption, "Old")

        latest_revision = page.get_latest_revision()
        self.assertNotEqual(page.live_revision_id, latest_revision.pk)
        self.assertEqual(latest_revision.content["title"], "New Draft Title")
        self.assertEqual(
            latest_revision.content["carousel_items"][0]["caption"], "New Draft Item"
        )

        latest_revision.publish()
        page.refresh_from_db()
        self.assertEqual(page.title, "New Draft Title")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "New Draft Item")

    def test_update_page_with_child_relation_unknown_id_is_treated_as_new(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home",
                slug="home-with-unknown-child-id",
                body="<p>hi</p>",
                live=False,
            )
        )
        item = page.carousel_items.create(
            caption="Old", link_external="http://example.com/old", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "carousel_items": [
                    {
                        "id": item.pk + 999,
                        "caption": "New",
                        "link_external": "http://example.com/new",
                    },
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        # The unmatched id is discarded entirely, not used as the new row's
        # pk - it's DB-autogenerated on insert, like any other new row.
        self.assertNotEqual(items[0].pk, item.pk)
        self.assertNotEqual(items[0].pk, item.pk + 999)
        self.assertEqual(items[0].caption, "New")

    def test_child_relations_untouched_when_omitted(self):
        page = self.root_page.add_child(
            instance=HomePage(
                title="Home", slug="home-untouched", body="<p>hi</p>", live=False
            )
        )
        # DeferringRelatedManager.create() only stages the child in memory -
        # it isn't written to the database until the parent is saved.
        page.carousel_items.create(
            caption="Kept", link_external="http://example.com/kept", sort_order=0
        )
        page.save()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.HomePage"},
                "title": "Home renamed",
            },
        )
        self.assertEqual(response.status_code, 200)
        page = HomePage.objects.get(pk=page.pk)
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].caption, "Kept")

    def test_update_page_with_foreign_key_field(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        page = self.root_page.add_child(
            instance=BlogEntryPage(
                title="Entry",
                slug="entry",
                body="<p>body</p>",
                date="2020-01-01",
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogEntryPage"},
                "feed_image_id": image.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.feed_image_id, image.pk)

    def test_update_page_with_foreign_key_field_omitted_is_untouched(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        page = self.root_page.add_child(
            instance=BlogEntryPage(
                title="Entry",
                slug="entry",
                body="<p>body</p>",
                date="2020-01-01",
                feed_image=image,
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogEntryPage"},
                "title": "Entry renamed",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.feed_image_id, image.pk)

    def test_update_page_with_foreign_key_field_set_to_null_clears_it(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        page = self.root_page.add_child(
            instance=BlogEntryPage(
                title="Entry",
                slug="entry",
                body="<p>body</p>",
                date="2020-01-01",
                feed_image=image,
                live=False,
            )
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogEntryPage"},
                "feed_image_id": None,
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertIsNone(page.feed_image_id)

    def test_omitted_meta_type_defaults_to_pages_own_type(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(page, {"title": "New title"})
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "New title")

    def test_falsy_meta_type_defaults_to_pages_own_type(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        falsy_values = [None, "", 0, [], {}]
        falsy_metas = falsy_values + [{"type": value} for value in falsy_values]
        for meta in falsy_metas:
            with self.subTest(meta=meta):
                response = self.patch(page, {"meta": meta, "title": "New title"})
                self.assertEqual(response.status_code, 200)
                page.refresh_from_db()
                self.assertEqual(page.title, "New title")

    def test_malformed_meta_type_returns_422(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        problem_metas = [
            (123, "123"),
            ("not a dict", "not a dict"),
            (["not", "a", "dict"], "['not', 'a', 'dict']"),
            ({"type": 123}, "123"),
            ({"type": ["not", "a", "string"]}, "['not', 'a', 'string']"),
            ({"type": self.user._meta.label}, self.user._meta.label),
            ({"type": Page._meta.label}, Page._meta.label),
        ]
        for meta, extracted in problem_metas:
            with self.subTest(meta=meta):
                response = self.patch(page, {"meta": meta, "title": "New title"})
                data = self.assert_problem_response(
                    response,
                    status_code=422,
                    detail_contains="Validation failed",
                    errors=[{"type": "union_tag_invalid", "loc": ["body", "data"]}],
                )
                self.assertEqual(len(data["errors"]), 1)
                self.assertIn(
                    f"Input tag '{extracted}' found using "
                    "discriminate_meta_type() does not match any of the expected "
                    "tags: ",
                    data["errors"][0]["msg"],
                )
                self.assertIn("demosite.BlogIndexPage", data["errors"][0]["msg"])

    def test_page_type_mismatch_returns_404(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.EventPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No EventPage matches the given query.",
        )

    def test_unknown_page_id_returns_404(self):
        response = self.client.patch(
            reverse("wagtailapi_v3:update_page", kwargs={"page_id": 999999}),
            data=json.dumps(
                {
                    "meta": {"type": "demosite.BlogIndexPage"},
                    "title": "New title",
                }
            ),
            content_type="application/json",
        )
        self.assert_problem_response(response, status_code=404)

    def test_user_without_change_permission_gets_403(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(response, status_code=403)

    def test_user_with_change_permission_on_branch_can_update(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                codename=Page.PERMISSION_CODENAMES.CHANGE,
            ),
        )
        self.login(username="editor", password="password")
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_user_with_change_but_not_publish_permission_with_publish_action(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                codename=Page.PERMISSION_CODENAMES.CHANGE,
            ),
        )
        self.login(username="editor", password="password")
        logs_since = timezone.now()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage", "action": "publish"},
                "title": "New title",
            },
        )
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="You do not have permission to publish this page.",
        )

        page.refresh_from_db()
        self.assertEqual(page.title, "Original")
        self.assertFalse(page.live)
        self.assertFalse(page.has_unpublished_changes)
        self.assertFalse(page.revisions.exists())
        self.assert_log_actions(page, [], since=logs_since)

    def test_update_page_when_locked_is_rejected(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        # Lock with no locked_by (e.g. locked by a script): applies to everyone
        page.locked = True
        page.save()

        logs_since = timezone.now()
        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="could not be saved as it is locked.",
        )

        # Nothing was saved, the page is unchanged, no draft/revision/log entry
        page.refresh_from_db()
        self.assertEqual(page.title, "Original")
        self.assertFalse(page.has_unpublished_changes)
        self.assertFalse(page.revisions.exists())
        self.assert_log_actions(page, [], since=logs_since)

    def test_update_page_when_locked_by_self_is_allowed(self):
        page = self.root_page.add_child(
            instance=BlogIndexPage(title="Original", slug="original", live=False)
        )
        page.locked = True
        page.locked_by = self.user
        page.locked_at = timezone.now()
        page.save()

        response = self.patch(
            page,
            {
                "meta": {"type": "demosite.BlogIndexPage"},
                "title": "New title",
            },
        )
        self.assertEqual(response.status_code, 200)
        page.refresh_from_db()
        self.assertEqual(page.title, "New title")
