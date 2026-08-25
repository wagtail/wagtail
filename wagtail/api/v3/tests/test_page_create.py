import json

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import GroupPagePermission, PageLogEntry, PageSubscription
from wagtail.test.demosite.models import (
    BlogEntryPage,
    BlogIndexPage,
    EventPage,
    HomePage,
)
from wagtail.test.testapp.models import SimpleParentPage, StreamPage
from wagtail.test.utils import Page, WagtailTestUtils


class TestV3PageCreate(TestV3Base, WagtailTestUtils, TestCase):
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

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=401)

    def test_superuser_can_create_page(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="new-page")
        self.assertEqual(page.title, "New page")
        self.assertEqual(page.get_parent().pk, self.root_page.pk)
        self.assertFalse(page.live)
        self.assertIsNone(page.live_revision)
        self.assertIsNone(page.first_published_at)
        self.assertIsNotNone(page.owner_id)

        content = response.json()
        self.assertEqual(content["title"], "New page")
        self.assertEqual(content["meta"]["type"], "demosite.BlogIndexPage")
        self.assertEqual(content["meta"]["slug"], "new-page")

    def test_create_page_with_publish_action_publishes_page(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                    "action": "publish",
                },
                "title": "Published page",
                "slug": "published-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="published-page")
        self.assertTrue(page.live)
        self.assertIsNotNone(page.live_revision)
        self.assertIsNotNone(page.first_published_at)
        self.assertEqual(page.live_revision, page.latest_revision)

    def test_create_page_with_invalid_action_returns_422(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                    "action": "not_a_real_action",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "literal_error",
                    "loc": [
                        "body",
                        "data",
                        "demosite.BlogIndexPage",
                        "meta",
                        "action",
                    ],
                    "msg": "Input should be 'publish'",
                    "ctx": {"expected": "'publish'"},
                }
            ],
        )
        self.assertIsNone(BlogIndexPage.objects.filter(slug="new-page").first())

    def test_create_page_subscribes_creator_to_comment_notifications(self):
        """
        Matches the admin create view, which subscribes the creating user to
        comment notifications on the new page by default.
        """
        user = self.user
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="new-page")
        subscription = PageSubscription.objects.get(page=page, user=user)
        self.assertTrue(subscription.comment_notifications)

    def test_create_saves_one_revision_and_matches_admin_log_entries(self):
        """
        add_child() saves the page directly, which already logs its own
        "wagtail.create" entry via Page.save() - so the router must not also
        use CreateAction (which would log a second, redundant "wagtail.create").
        The real admin create view logs "wagtail.create" (from add_child's
        save) plus "wagtail.edit" (from save_revision(log_action=True)) for
        every new page; this asserts the API produces that same pair, not a
        duplicate "wagtail.create".
        """
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "Logged page",
                "slug": "logged-page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="logged-page")

        self.assertEqual(page.revisions.count(), 1)
        self.assertIsNotNone(page.latest_revision)

        actions = list(
            PageLogEntry.objects.filter(page=page)
            .order_by("timestamp")
            .values_list("action", flat=True)
        )
        self.assertEqual(actions, ["wagtail.create", "wagtail.edit"])

    def test_superuser_can_create_page_with_api_field(self):
        """
        Only fields listed in a page model's api_fields as
        APIField(name, writable=True) (plus the base
        title/slug/seo_title/search_description/show_in_menus) are writable.
        A model with a required panel field that isn't marked writable can't
        have that field set via this endpoint: the real admin form used for
        validation will reject the create for missing that field, since it
        isn't exposed in the input schema. StreamPage's body is marked
        writable, so it's fully creatable.
        """
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "api-field-page",
                "body": [{"type": "text", "value": "hello world"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="api-field-page")
        self.assertEqual(page.body[0].value, "hello world")

    def test_create_page_with_non_writable_api_field_ignores_it(self):
        """
        BlogIndexPage.intro is a real model field listed in api_fields, but
        not as APIField("intro", writable=True) - so it's read-only via this
        API and posting it is silently ignored, not an error.
        """
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
                "intro": "should be ignored",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="new-page")
        self.assertEqual(page.intro, "")

    def test_create_page_with_field_not_in_api_fields_ignores_it(self):
        """
        Page.live is a real model field, but isn't listed in BlogIndexPage's
        api_fields at all - posting it is silently ignored, not an error.
        """
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
                "live": True,
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(slug="new-page")
        self.assertFalse(page.live)

    def test_create_page_with_non_model_field_in_api_fields_ignores_it(self):
        """
        AbstractLinkFields.link is listed in api_fields but is a Python
        @property, not a real Django field - it has no defined writable
        shape, so posting it (here nested in a HomePage carousel item) is
        silently ignored, not an error.
        """
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-with-link-property",
                "carousel_items": [
                    {
                        "caption": "First",
                        "link_external": "http://example.com/real",
                        "link": "http://should-be-ignored.example",
                    },
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = HomePage.objects.get(slug="home-with-link-property")
        item = page.carousel_items.get()
        self.assertEqual(item.caption, "First")
        self.assertEqual(item.link_external, "http://example.com/real")
        self.assertEqual(item.link, "http://example.com/real")

    def test_create_page_with_non_writable_api_field_in_inline_model_ignores_it(self):
        """
        EventPageSpeaker.link_document is a real model field listed in
        api_fields, but not as APIField("link_document", writable=True) - so
        it's read-only via this API and posting it (nested in an EventPage's
        speakers InlinePanel) is silently ignored, not an error. link_external
        is writable, so it's set as normal, and the link property (also
        listed in api_fields, but never writable) resolves from it.
        """
        document = Document.objects.create(title="Test document")
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.EventPage"},
                "title": "New page",
                "slug": "new-page",
                "date_from": "2026-07-21",
                "audience": "public",
                "location": "",
                "cost": "",
                "speakers": [
                    {
                        "first_name": "Jane",
                        "link_external": "http://example.com/speaker",
                        "link_document": document.pk,
                    },
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = EventPage.objects.get(slug="new-page")
        speaker = page.speakers.get()
        self.assertEqual(speaker.first_name, "Jane")
        self.assertIsNone(speaker.link_document)
        self.assertEqual(speaker.link_external, "http://example.com/speaker")
        self.assertEqual(speaker.link, "http://example.com/speaker")

    def test_create_page_with_unknown_field_ignores_it(self):
        """
        A field that's neither a real model field nor listed in api_fields
        at all is silently ignored, not an error.
        """
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
                "not_a_real_field_at_all": "should be ignored",
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(BlogIndexPage.objects.filter(slug="new-page").exists())

    def test_slug_is_auto_generated_from_title_when_omitted(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "Auto Slug Page",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogIndexPage.objects.get(title="Auto Slug Page")
        self.assertEqual(page.slug, "auto-slug-page")

    def test_duplicate_slug_returns_422(self):
        self.root_page.add_child(
            instance=BlogIndexPage(title="Existing", slug="existing")
        )
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "Another",
                "slug": "existing",
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "invalid",
                    "loc": ["slug"],
                    "msg": "The slug 'existing' is already in use within the parent page.",
                }
            ],
        )

    def test_missing_required_field_returns_422(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "slug": "no-title",
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "missing",
                    "loc": [
                        "body",
                        "data",
                        "demosite.BlogIndexPage",
                        "title",
                    ],
                    "msg": "Field required",
                }
            ],
        )

    def test_page_type_with_required_field_can_be_saved_as_draft(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.EventPage"},
                "title": "New page",
                "slug": "new-page",
                "date_from": "2026-07-21",
                "audience": "public",
                "location": "",
                "cost": "",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = EventPage.objects.get(slug="new-page")
        self.assertFalse(page.live)
        self.assertEqual(page.location, "")

    def test_page_type_with_missing_required_field_returns_422_on_publish(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.EventPage",
                    "action": "publish",
                },
                "title": "New page",
                "slug": "new-page",
                "date_from": "2026-07-21",
                "audience": "public",
                "location": "",
                "cost": "",
                "signup_link": "http://example.com/signup",
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "required",
                    "loc": ["location"],
                    "msg": "This field is required.",
                },
                {
                    "type": "required",
                    "loc": ["cost"],
                    "msg": "This field is required.",
                },
            ],
        )

    def test_api_base_form_class(self):
        """
        EventPage has API-specific api_base_form_class with a custom validation
        rule that requires signup_link to be set when publishing an event.
        """
        payload = {
            "meta": {
                "parent_id": self.root_page.pk,
                "type": "demosite.EventPage",
            },
            "title": "New page as draft",
            "slug": "new-page-as-draft",
            "date_from": "2026-07-21",
            "audience": "public",
            "location": "Somewhere",
            "cost": "Free",
        }
        response = self.post(payload)
        self.assertEqual(response.status_code, 201)
        page = EventPage.objects.get(slug="new-page-as-draft")
        self.assertFalse(page.live)
        self.assertEqual(page.signup_link, "")

        response = self.post(
            {
                **payload,
                "meta": {**payload["meta"], "action": "publish"},
                "title": "New page to publish",
                "slug": "new-page-to-publish",
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "invalid",
                    "loc": ["signup_link"],
                    "msg": "This field is required when publishing events via the API.",
                }
            ],
        )

    def test_unknown_parent_returns_404(self):
        response = self.post(
            {
                "meta": {"parent_id": 999999, "type": "demosite.BlogIndexPage"},
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=404)

    def test_malformed_meta_type_returns_422(self):
        problem_metas = [
            (123, "123"),
            ("not a dict", "not a dict"),
            (["not", "a", "dict"], "['not', 'a', 'dict']"),
            ({"type": 123}, "123"),
            ({"type": ["not", "a", "string"]}, "['not', 'a', 'string']"),
            ({"parent_id": self.root_page.pk}, ""),
            ({"parent_id": self.root_page.pk, "type": 123}, "123"),
            (
                {"parent_id": self.root_page.pk, "type": ["not", "a", "string"]},
                "['not', 'a', 'string']",
            ),
            ({"parent_id": self.root_page.pk, "type": "not.AType"}, "not.AType"),
            ({"parent_id": self.root_page.pk, "type": "auth.User"}, "auth.User"),
            (
                {"parent_id": self.root_page.pk, "type": Page._meta.label},
                Page._meta.label,
            ),
        ]
        for meta, extracted in problem_metas:
            with self.subTest(meta=meta):
                data = {"meta": meta, "title": "New page", "slug": "new-page"}
                response = self.post(data)
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

    def test_user_without_add_permission_gets_403(self):
        self.create_user(username="noperms", password="password")
        self.login(username="noperms", password="password")
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=403)

    def test_user_with_add_permission_on_branch_can_create(self):
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                codename=Page.PERMISSION_CODENAMES.ADD,
            ),
        )
        self.login(username="editor", password="password")
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_user_with_add_but_not_publish_permission_with_publish_action(self):
        editor = self.create_user(username="editor", password="password")
        editor_group = Group.objects.create(name="Page branch editors")
        editor.groups.add(editor_group)
        GroupPagePermission.objects.create(
            group=editor_group,
            page=self.root_page,
            permission=Permission.objects.get(
                codename=Page.PERMISSION_CODENAMES.ADD,
            ),
        )
        self.login(username="editor", password="password")
        logs_before = PageLogEntry.objects.count()
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogIndexPage",
                    "action": "publish",
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="You do not have permission to publish this page.",
        )

        self.assertIsNone(BlogIndexPage.objects.filter(slug="new-page").first())
        self.assertEqual(PageLogEntry.objects.count(), logs_before)

    def test_disallowed_subpage_type_returns_403(self):
        parent = self.root_page.add_child(
            instance=SimpleParentPage(title="Parent", slug="parent-page")
        )
        response = self.post(
            {
                "meta": {
                    "parent_id": parent.pk,
                    # SimpleParentPage only allows SimpleChildPage as subpages,
                    # so this should be rejected.
                    "type": HomePage._meta.label,
                },
                "title": "New page",
                "slug": "new-page",
            }
        )
        self.assert_problem_response(response, status_code=403)

    def test_create_streamfield_page(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page",
                "body": [{"type": "text", "value": "hello streamfield"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="stream-page")
        self.assertEqual(len(page.body), 1)
        self.assertEqual(page.body[0].block_type, "text")
        self.assertEqual(page.body[0].value, "hello streamfield")

    def test_create_streamfield_page_with_invalid_block_type_returns_422(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page-invalid",
                "body": [{"type": "not_a_real_block", "value": "hello"}],
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [{"msg": "body: unrecognised block type 'not_a_real_block'"}],
        )

    def test_create_streamfield_page_with_rich_text_block(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page-rich-text",
                "body": [{"type": "rich_text", "value": "<p>hello <b>world</b></p>"}],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="stream-page-rich-text")
        self.assertEqual(page.body[0].block_type, "rich_text")
        self.assertIn("hello <b>world</b>", str(page.body[0].value))

    def test_create_streamfield_page_with_various_block_types(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        table = {
            "data": [["", "Column"], ["Row", "Value"]],
            "first_col_is_header": True,
            "first_row_is_table_header": True,
            "mergeCells": [],
            "table_caption": "Minimal API table",
            "table_header_choice": "both",
        }
        cases = [
            (
                "text",
                "hello streamfield",
                lambda value: self.assertEqual(value, "hello streamfield"),
                lambda value: self.assertEqual(value, "hello streamfield"),
            ),
            (
                "product",
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
                "<div>raw</div>",
                lambda value: self.assertEqual(str(value), "<div>raw</div>"),
                lambda value: self.assertEqual(value, "<div>raw</div>"),
            ),
            (
                "books",
                [
                    {"type": "title", "value": "Dune"},
                    {"type": "author", "value": "Frank Herbert"},
                ],
                lambda value: (
                    self.assertEqual(value[0].block_type, "title"),
                    self.assertEqual(value[0].value, "Dune"),
                    self.assertEqual(value[1].block_type, "author"),
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
                ["First", "Second", "Third"],
                lambda value: self.assertEqual(
                    list(value), ["First", "Second", "Third"]
                ),
                lambda value: self.assertEqual(value, ["First", "Second", "Third"]),
            ),
            (
                "image",
                image.pk,
                lambda value: self.assertEqual(value.pk, image.pk),
                lambda value: self.assertEqual(value, image.pk),
            ),
            (
                "image_with_alt",
                {
                    "image": image.pk,
                    "decorative": False,
                    "alt_text": "A test image",
                },
                lambda value: (
                    self.assertEqual(value.pk, image.pk),
                    self.assertEqual(value.contextual_alt_text, "A test image"),
                ),
                lambda value: self.assertEqual(
                    value,
                    {
                        "image": image.pk,
                        "decorative": False,
                        "alt_text": "A test image",
                    },
                ),
            ),
            (
                "table",
                table,
                lambda value: self.assertEqual(value, table),
                lambda value: self.assertEqual(value, table),
            ),
        ]
        for (
            block_type,
            input_value,
            assert_db_value,
            assert_api_value,
        ) in cases:
            with self.subTest(block_type=block_type):
                slug = f"stream-page-{block_type}"
                response = self.post(
                    {
                        "meta": {
                            "parent_id": self.root_page.pk,
                            "type": "tests.StreamPage",
                        },
                        "title": "Stream page",
                        "slug": slug,
                        "body": [{"type": block_type, "value": input_value}],
                    }
                )
                self.assertEqual(response.status_code, 201)

                page = StreamPage.objects.get(slug=slug)
                self.assertEqual(page.body[0].block_type, block_type)
                assert_db_value(page.body[0].value)

                [block] = response.json()["body"]
                self.assertEqual(block["type"], block_type)
                self.assertTrue(block["id"])
                assert_api_value(block["value"])

    def test_create_streamfield_page_with_image_chooser_block_extended(self):
        """
        With an ?extended= query param, ExtendedImageChooserBlock's
        get_api_representation returns a dict of id/title instead of a bare
        pk. Ensure this is respected in the create response body.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.client.post(
            reverse("wagtailapi_v3:create_page") + "?extended=true",
            data=json.dumps(
                {
                    "meta": {
                        "parent_id": self.root_page.pk,
                        "type": "tests.StreamPage",
                    },
                    "title": "Stream page",
                    "slug": "stream-page-image-extended",
                    "body": [{"type": "image", "value": image.pk}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        content = response.json()
        [block] = content["body"]
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["value"], {"id": image.pk, "title": image.title})

    def test_create_streamfield_page_with_multiple_blocks(self):
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "tests.StreamPage"},
                "title": "Stream page",
                "slug": "stream-page-multiple",
                "body": [
                    {"type": "text", "value": "hello"},
                    {"type": "rich_text", "value": "<p>hi</p>"},
                    {"type": "image", "value": image.pk},
                    {
                        "type": "product",
                        "value": {"name": "Widget", "price": "9.99"},
                    },
                    {"type": "raw_html", "value": "<hr>"},
                    {
                        "type": "books",
                        "value": [
                            {"type": "title", "value": "Dune"},
                            {"type": "author", "value": "Frank Herbert"},
                        ],
                    },
                    {"type": "title_list", "value": ["First", "Second"]},
                    {
                        "type": "image_with_alt",
                        "value": {
                            "image": image.pk,
                            "decorative": False,
                            "alt_text": "A test image",
                        },
                    },
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = StreamPage.objects.get(slug="stream-page-multiple")
        self.assertEqual(len(page.body), 8)
        self.assertEqual(
            [block.block_type for block in page.body],
            [
                "text",
                "rich_text",
                "image",
                "product",
                "raw_html",
                "books",
                "title_list",
                "image_with_alt",
            ],
        )

    def test_create_page_with_rich_text_field(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-rich-text",
                "body": "<p>hello</p>",
                "carousel_items": [],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = HomePage.objects.get(slug="home-rich-text")
        self.assertIn("hello", page.body)

    def test_create_page_with_child_relations(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-with-children",
                "body": "<p>hi</p>",
                "carousel_items": [
                    {
                        "caption": "First",
                        "embed_url": "http://example.com/1",
                        "link_external": "http://example.com/1",
                    },
                    {
                        "caption": "Second",
                        "embed_url": "http://example.com/2",
                        "link_external": "http://example.com/2",
                    },
                ],
            }
        )
        self.assertEqual(response.status_code, 201)
        page = HomePage.objects.get(slug="home-with-children")
        items = list(page.carousel_items.order_by("sort_order"))
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].caption, "First")
        self.assertEqual(items[1].caption, "Second")
        self.assertEqual(items[0].sort_order, 0)
        self.assertEqual(items[1].sort_order, 1)

    def test_create_page_with_invalid_child_relation_field_returns_422(self):
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-invalid-child",
                "body": "<p>hi</p>",
                "carousel_items": [
                    {
                        "caption": "x" * 1000,
                        "embed_url": "http://example.com/1",
                        "link_external": "http://example.com/1",
                    },
                ],
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "string_too_long",
                    "loc": [
                        "body",
                        "data",
                        "demosite.HomePage",
                        "carousel_items",
                        0,
                        "caption",
                    ],
                    "msg": "String should have at most 255 characters",
                    "ctx": {"max_length": 255},
                }
            ],
        )

    def test_create_page_with_foreign_key_field(self):
        """
        BlogEntryPage.feed_image is a writable ForeignKey APIField, exposed
        on the input schema as feed_image_id - posting the related object's
        pk sets the relation.
        """
        image = Image.objects.create(title="Test image", file=get_test_image_file())
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogEntryPage",
                },
                "title": "New entry",
                "slug": "new-entry",
                "body": "<p>body</p>",
                "date": "2020-01-01",
                "feed_image_id": image.pk,
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogEntryPage.objects.get(slug="new-entry")
        self.assertEqual(page.feed_image_id, image.pk)

    def test_create_page_with_foreign_key_field_omitted_is_null(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogEntryPage",
                },
                "title": "New entry",
                "slug": "new-entry-no-image",
                "body": "<p>body</p>",
                "date": "2020-01-01",
            }
        )
        self.assertEqual(response.status_code, 201)
        page = BlogEntryPage.objects.get(slug="new-entry-no-image")
        self.assertIsNone(page.feed_image_id)

    def test_create_page_with_unknown_foreign_key_id_returns_422(self):
        response = self.post(
            {
                "meta": {
                    "parent_id": self.root_page.pk,
                    "type": "demosite.BlogEntryPage",
                },
                "title": "New entry",
                "slug": "new-entry-bad-image",
                "body": "<p>body</p>",
                "date": "2020-01-01",
                "feed_image_id": 999999,
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "invalid_choice",
                    "loc": ["feed_image"],
                    "msg": (
                        "Select a valid choice. That choice is not one of "
                        "the available choices."
                    ),
                }
            ],
        )

    def test_create_page_with_child_relation_missing_link_returns_422(self):
        """
        AbstractLinkFields.clean() (a custom cross-field validator on
        HomePageCarouselItem's own form) requires a related page, document,
        or external URL - this is real form-level validation, not something
        the input schema itself can express, and it runs because we validate
        through the model's actual admin form rather than bypassing it.
        """
        response = self.post(
            {
                "meta": {"parent_id": self.root_page.pk, "type": "demosite.HomePage"},
                "title": "Home",
                "slug": "home-missing-link",
                "body": "<p>hi</p>",
                "carousel_items": [{"caption": "No link"}],
            }
        )
        content = self.assert_problem_response(response, status_code=422)
        self.assertEqual(
            content["errors"],
            [
                {
                    "type": "invalid",
                    "loc": ["carousel_items", 0, "__all__"],
                    "msg": "You must provide a related page, related document or an external URL",
                }
            ],
        )
