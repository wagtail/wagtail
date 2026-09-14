import json

from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.models import GroupPagePermission, Locale, PageLogEntry
from wagtail.test.i18n.models import TestPage
from wagtail.test.testapp.models import (
    EventIndex,
    EventPage,
    PageWithExcludedCopyField,
    SimplePage,
)
from wagtail.test.utils import Page, PageFixturesMixin

from .utils import AdminAPITestCase


class TestCopyPageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
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

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
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
            content,
            {"detail": ("You do not have permission to copy this page")},
        )

    def test_respects_page_creation_rules(self):
        # Only one homepage may exist
        response = self.get_response(2, {})

        self.assertEqual(response.status_code, 403)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"detail": "You do not have permission to copy this page"}
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
                    "The slug 'events' is already in use within the parent page at '/'."
                ]
            },
        )


class TestConvertAliasPageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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
        self.assertEqual(log.page, self.alias_page.get_base_page())
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
        self.assertEqual(response.status_code, 404)


class TestDeletePageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
        )

        # Page is still there
        self.assertTrue(Page.objects.filter(id=4).exists())


class TestPublishPageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
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


class TestUnpublishPageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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

        self.assertEqual(response.status_code, 404)
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
        )


class TestMovePageAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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
        self.assertEqual(response.status_code, 404)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
        )

    def test_move_page_without_destination_page_id(self):
        response = self.get_response(4, {})
        self.assertEqual(response.status_code, 400)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, {"destination_page_id": ["This field is required."]})


class TestCopyForTranslationAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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
        self.assertEqual(
            content,
            {
                "message": "Parent page 'Welcome to the Wagtail test site!' "
                "is not translated."
            },
        )

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

    def test_translating_latest_non_draft_page_revision(self):
        old_index_title = self.en_eventindex.title
        old_post_title = self.en_eventpage.title
        new_index_title = old_index_title + "-77777"
        new_post_title = old_post_title + "-77777"
        self.en_eventindex.title = new_index_title
        self.en_eventindex.save_revision(log_action=True)
        self.en_eventpage.title = new_post_title
        self.en_eventpage.save_revision(log_action=True)

        response = self.get_response(
            self.en_eventindex.id,
            {"locale": "fr", "copy_parents": True, "recursive": True},
        )

        assert response.status_code == 201

        new_index_page = [
            trans_page
            for trans_page in self.en_eventindex.get_translations()
            if trans_page.locale.language_code == "fr"
        ][0]
        assert new_index_page.title == old_index_title
        new_post_page = [
            trans_page
            for trans_page in self.en_eventpage.get_translations()
            if trans_page.locale.language_code == "fr"
        ][0]
        assert new_post_page.title == old_post_title

    def test_translating_latest_draft_page_revision(self):
        """In case when Page have only draft revisions"""

        draft_index_page = TestPage(title="Draft Blog", slug="draft_blog", live=False)
        self.en_homepage.add_child(instance=draft_index_page)
        draft_blog_post = TestPage(
            title="Draft Blog post", slug="draft_blog-post", live=False
        )
        draft_index_page.add_child(instance=draft_blog_post)

        old_index_title = draft_index_page.title
        new_index_title = old_index_title + "-77777"
        draft_index_page.title = new_index_title
        draft_index_page.save_revision(log_action=True)

        old_page_title = draft_blog_post.title
        new_page_title = old_page_title + "-77777"
        draft_blog_post.title = new_page_title
        draft_blog_post.save_revision(log_action=True)

        response = self.get_response(
            draft_index_page.id,
            {"locale": "fr", "copy_parents": True, "recursive": True},
        )

        assert response.status_code == 201

        new_index_page = [
            trans_page
            for trans_page in draft_index_page.get_translations()
            if trans_page.locale.language_code == "fr"
        ][0]
        assert new_index_page.title == new_index_title
        new_post_page = [
            trans_page
            for trans_page in draft_blog_post.get_translations()
            if trans_page.locale.language_code == "fr"
        ][0]
        assert new_post_page.title == new_page_title

    def test_without_translate_permission(self):
        self.user.is_superuser = False
        editors = Group.objects.get(name="Editors")
        GroupPagePermission.objects.create(
            group=editors, page_id=self.root_page.id, permission_type="change"
        )
        self.user.groups.add(editors)
        self.user.save()

        response = self.get_response(self.en_homepage.id, {"locale": "fr"})

        self.assertEqual(response.status_code, 403)

    def test_without_edit_permission(self):
        self.user.is_superuser = False
        editors = Group.objects.get(name="Editors")
        editors.permissions.add(
            Permission.objects.get(
                content_type__app_label="simple_translation",
                codename="submit_translation",
            )
        )
        # Grant edit permission over a page that is not the one being copied
        GroupPagePermission.objects.create(
            group=editors, page_id=self.en_eventindex.id, permission_type="change"
        )

        self.user.groups.add(editors)
        self.user.save()

        response = self.get_response(self.en_homepage.id, {"locale": "fr"})

        self.assertEqual(response.status_code, 403)

    def test_with_translate_and_edit_permissions(self):
        self.user.is_superuser = False
        editors = Group.objects.get(name="Editors")
        editors.permissions.add(
            Permission.objects.get(
                content_type__app_label="simple_translation",
                codename="submit_translation",
            )
        )
        GroupPagePermission.objects.create(
            group=editors, page_id=self.root_page.id, permission_type="change"
        )
        self.user.groups.add(editors)
        self.user.save()

        response = self.get_response(self.en_homepage.id, {"locale": "fr"})

        self.assertEqual(response.status_code, 201)


class TestCreatePageAliasAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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
        self.assertEqual(response.status_code, 404)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
        )


class TestRevertToPageRevisionAction(PageFixturesMixin, AdminAPITestCase, TestCase):
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
        self.assertEqual(response.status_code, 404)

        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(
            content, {"message": f"No {Page.__name__} matches the given query."}
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
