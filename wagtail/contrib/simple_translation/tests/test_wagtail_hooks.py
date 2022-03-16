from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.contrib.simple_translation.wagtail_hooks import (
    page_listing_more_buttons,
    register_submit_translation_permission,
)
from wagtail.core import hooks
from wagtail.core.actions.create_alias import CreatePageAliasAction
from wagtail.core.actions.move_page import MovePageAction
from wagtail.core.models import Locale, Page
from wagtail.tests.i18n.models import TestPage
from wagtail.tests.utils import WagtailTestUtils


class Utils(WagtailTestUtils, TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.first()
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.de_locale = Locale.objects.create(language_code="de")

        self.en_homepage = Page.objects.get(depth=2)
        self.fr_homepage = self.en_homepage.copy_for_translation(self.fr_locale)
        self.de_homepage = self.en_homepage.copy_for_translation(self.de_locale)

        self.en_blog_index = TestPage(title="Blog", slug="blog")
        self.en_homepage.add_child(instance=self.en_blog_index)

        self.en_blog_post = TestPage(title="Blog post", slug="blog-post")
        self.en_blog_index.add_child(instance=self.en_blog_post)


class TestWagtailHooksURLs(TestCase):
    def test_register_admin_urls_page(self):
        self.assertEqual(
            reverse("simple_translation:submit_page_translation", args=(1,)),
            "/admin/translation/submit/page/1/",
        )

    def test_register_admin_urls_snippet(self):
        app_label = "foo"
        model_name = "bar"
        pk = 1
        self.assertEqual(
            reverse(
                "simple_translation:submit_snippet_translation",
                args=(app_label, model_name, pk),
            ),
            "/admin/translation/submit/snippet/foo/bar/1/",
        )


class TestWagtailHooksPermission(Utils):
    def test_register_submit_translation_permission(self):
        assert list(
            register_submit_translation_permission().values_list("id", flat=True)
        ) == [
            Permission.objects.get(
                content_type__app_label="simple_translation",
                codename="submit_translation",
            ).id
        ]


class TestWagtailHooksButtons(Utils):
    class PagePerms:
        def __init__(self, user):
            self.user = user

    def test_page_listing_more_buttons(self):
        # Root, no button
        root_page = self.en_blog_index.get_root()

        if get_user_model().USERNAME_FIELD == "email":
            user = get_user_model().objects.create_user(email="jos@example.com")
        else:
            user = get_user_model().objects.create_user(username="jos")
        assert list(page_listing_more_buttons(root_page, self.PagePerms(user))) == []

        # No permissions, no button
        home_page = self.en_homepage
        assert list(page_listing_more_buttons(root_page, self.PagePerms(user))) == []

        # Homepage is translated to all languages, no button
        perm = Permission.objects.get(codename="submit_translation")

        if get_user_model().USERNAME_FIELD == "email":
            user = get_user_model().objects.create_user(email="henk@example.com")
        else:
            user = get_user_model().objects.create_user(username="henk")

        # New user, to prevent permission cache.
        user.user_permissions.add(perm)
        group = Group.objects.get(name="Editors")
        user.groups.add(group)
        page_perms = self.PagePerms(user)
        assert list(page_listing_more_buttons(home_page, page_perms)) == []

        # Page does not have translations yet... button!
        blog_page = self.en_blog_post
        assert isinstance(
            list(page_listing_more_buttons(blog_page, page_perms))[0],
            wagtailadmin_widgets.Button,
        )


class TestConstructSyncedPageTreeListHook(Utils):
    def unpublish_hook(self, pages, action):
        self.assertEqual(action, "unpublish")
        self.assertIsInstance(pages, list)

    def missing_hook_action(self, pages, action):
        self.assertEqual(action, "")
        self.assertIsInstance(pages, list)

    def test_double_registered_hook(self):
        # We should have two implementations of `construct_synced_page_tree_list`
        # One in simple_translation.wagtail_hooks and the other will be
        # registered as a temporary hook.
        with hooks.register_temporarily(
            "construct_synced_page_tree_list", self.unpublish_hook
        ):
            defined_hooks = hooks.get_hooks("construct_synced_page_tree_list")
            self.assertEqual(len(defined_hooks), 2)

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True)
    def test_page_tree_sync_on(self):
        with hooks.register_temporarily(
            "construct_synced_page_tree_list", self.unpublish_hook
        ):
            for fn in hooks.get_hooks("construct_synced_page_tree_list"):
                response = fn([self.en_homepage], "unpublish")
                if response:
                    self.assertIsInstance(response, dict)
                    self.assertEqual(len(response.items()), 1)

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=False)
    def test_page_tree_sync_off(self):
        with hooks.register_temporarily(
            "construct_synced_page_tree_list", self.unpublish_hook
        ):
            for fn in hooks.get_hooks("construct_synced_page_tree_list"):
                response = fn([self.en_homepage], "unpublish")
                self.assertIsNone(response)

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True)
    def test_missing_hook_action(self):
        with hooks.register_temporarily(
            "construct_synced_page_tree_list", self.missing_hook_action
        ):
            for fn in hooks.get_hooks("construct_synced_page_tree_list"):
                response = fn([self.en_homepage], "")
                if response is not None:
                    self.assertIsInstance(response, dict)

    @override_settings(
        WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True, WAGTAIL_I18N_ENABLED=True
    )
    def test_other_l10n_pages_were_unpublished(self):
        # Login to access the admin
        self.login()

        # Make sur the French homepage is published/live
        self.fr_homepage.live = True
        self.fr_homepage.save()
        self.assertTrue(self.en_homepage.live)
        self.assertTrue(self.fr_homepage.live)

        response = self.client.post(
            reverse("wagtailadmin_pages:unpublish", args=(self.en_homepage.id,)),
            {"include_descendants": False},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Refresh objects from the database
        self.en_homepage.refresh_from_db()
        self.fr_homepage.refresh_from_db()

        # Test that both the English and French homepages are unpublished
        self.assertFalse(self.en_homepage.live)
        self.assertFalse(self.fr_homepage.live)


@override_settings(
    WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True, WAGTAIL_I18N_ENABLED=True
)
class TestDeletingTranslatedPages(Utils):
    def delete_hook(self, pages, action):
        self.assertEqual(action, "delete")
        self.assertIsInstance(pages, list)

    def test_construct_synced_page_tree_list_when_deleting(self):
        with hooks.register_temporarily(
            "construct_synced_page_tree_list", self.delete_hook
        ):
            for fn in hooks.get_hooks("construct_synced_page_tree_list"):
                response = fn([self.en_homepage], "delete")
                if response is not None:
                    self.assertIsInstance(response, dict)
                    self.assertEqual(len(response.items()), 1)

    def test_delete_translated_pages(self):
        # Login to the Wagtail admin with a superuser account
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        # Create a copy of the en_blog_post object as a translated page
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)

        # 1. Delete the en_blog_post by making a POST request to /delete/
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:delete",
                args=(self.en_blog_post.id,),
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # 2. Confirm fr_blog_post is deleted
        self.assertIsNone(Page.objects.filter(pk=self.fr_blog_post.id).first())

    def test_delete_confirmation_template(self):
        """Test the context info is correct in the confirm_delete.html template."""
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        # Create a copy of the en_blog_post object as a translated page
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)

        # Create an alias page to test the `translations_to_move_count`
        # in the template context
        new_page = CreatePageAliasAction(
            self.en_blog_post,
            recursive=False,
            parent=self.en_blog_index,
            update_slug="alias-page-slug",
            user=None,
        )
        new_page.execute(skip_permission_checks=True)

        response = self.client.get(
            reverse(
                "wagtailadmin_pages:delete",
                args=(self.en_blog_post.id,),
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["translation_count"], 1)
        self.assertEqual(response.context["translation_descendant_count"], 0)
        self.assertIn(
            "Deleting this page will also delete 1 translation of this page.",
            response.content.decode("utf-8"),
        )

    def test_deleting_page_with_divergent_translation_tree(self):
        self.login()

        # New parent to eventually hold the fr_blog_post object.
        self.en_new_parent = TestPage(title="Test Parent", slug="test-parent")
        self.en_homepage.add_child(instance=self.en_new_parent)

        # Copy the /blog/ and French /blog-post/ pages.
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)
        # Copy the en new parent to be a french page
        self.fr_new_parent = self.en_new_parent.copy_for_translation(self.fr_locale)

        # Manually move the fr_blog_post to live under fr_new_parent
        # Because this does not go through the POST request in pages/move.py
        # this action will create a diverged tree scnenario where en_blog_post
        # and fr_blog_post don't mirror their original positions in the tree.
        action = MovePageAction(
            self.fr_blog_post,
            self.fr_new_parent,
            pos="last-child",
            user=None,
        )
        action.execute(skip_permission_checks=True)

        self.fr_blog_post.refresh_from_db()
        self.en_blog_post.refresh_from_db()

        # Confirm fr_blog_post parent id is the fr_new_parent id.
        # Confirm en_blog_post parent id is the en_blog_index id
        self.assertEqual(
            self.fr_blog_post.get_parent(update=True).id, self.fr_new_parent.id
        )
        self.assertEqual(
            self.en_blog_post.get_parent(update=True).id, self.en_blog_index.id
        )

        # Make a post request to move the en_blog_post to live under en_homepage
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:delete",
                args=(self.en_blog_post.id,),
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        # Confirm that the en_blog_post object no longer exists.
        self.assertFalse(Page.objects.filter(pk=self.en_blog_post.id).exists())
        # Confirm that the fr_blog_post object stll exists, because it was moved
        self.assertTrue(Page.objects.filter(pk=self.fr_blog_post.id).exists())

        # Confirm the fr_blog_post parent id matches the new_parent_page id
        # This confirms is hasn't moved and hasn't been deleted.
        # to a different location in the tree.
        self.fr_blog_post.refresh_from_db()
        self.assertEqual(
            self.fr_blog_post.get_parent(update=True).id, self.fr_new_parent.id
        )

    def test_alias_pages_when_deleting_source_page(self):
        """
        When deleting a page that has an alias page, the alias page should
        continue to exist while the original original page should be deleted
        while using the `construct_synced_page_tree_list` hook is active.
        """
        self.login()

        # Test the source page exists in the right tree location
        self.assertEqual(self.en_blog_post.get_parent().id, self.en_blog_index.id)

        # Create an alias page from en_blog_post
        action = CreatePageAliasAction(
            self.en_blog_post,
            recursive=False,
            parent=self.en_blog_index,
            update_slug="sample-slug",
            user=None,
        )
        new_page = action.execute(skip_permission_checks=True)
        # Make sure the alias page is an alias of the en_blog_post
        # and exists under the same parent page.
        self.assertEqual(new_page.get_parent().id, self.en_blog_index.id)
        # Test alias of source page
        self.assertEqual(new_page.alias_of_id, self.en_blog_post.id)

        # Delete the en_blog_post page and make sure the alias page is kept in tact.
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:delete",
                args=(self.en_blog_post.id,),
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Page.objects.filter(pk=self.en_blog_post.id).exists())
        self.assertTrue(Page.objects.filter(pk=new_page.id).exists())

    def test_translation_alias_pages_when_deleting_source_page(self):
        """
        When deleting a page that has an alias page, the alias page
        should be deleted while using the `construct_synced_page_tree_list`
        hook is active.
        """
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        # Create a copy of the en_blog_post object as a translated alias page
        self.fr_blog_post = self.en_blog_post.copy_for_translation(
            self.fr_locale, alias=True
        )
        self.assertEqual(self.fr_blog_post.alias_of_id, self.en_blog_post.id)
        self.assertEqual(self.fr_blog_post.get_parent().id, self.fr_blog_index.id)

        # Test fr_blog_post alias_id is in the list of translations
        # Test fr_blog_post is a proper alias of en_blog_post
        # Test fr_blog_post is using the french locale (fr)
        # Test beyond the language code to ensure the page is in the correct language tree
        translation_ids = [p.id for p in self.fr_blog_post.get_translations()]
        self.assertIn(self.fr_blog_post.alias_of_id, translation_ids)
        self.assertEqual(self.fr_blog_post.alias_of_id, self.en_blog_post.id)
        self.assertEqual(self.fr_blog_post.locale.language_code, "fr")

        # Test the source is in the source tree root (source HomePage)
        # Test that the translated alias is in the translated root (fr HomePage)
        en_root = Page.objects.filter(depth__gt=1, locale=self.en_locale).first()
        fr_root = Page.objects.filter(depth__gt=1, locale=self.fr_locale).first()
        self.assertIn(self.en_blog_post, en_root.get_descendants().specific())
        self.assertIn(self.fr_blog_post, fr_root.get_descendants().specific())

        # Delete the en_blog_post page and make sure the alias page is kept in tact.
        response = self.client.post(
            reverse(
                "wagtailadmin_pages:delete",
                args=(self.en_blog_post.id,),
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Page.objects.filter(pk=self.en_blog_post.id).exists())
        self.assertFalse(Page.objects.filter(pk=self.fr_blog_post.id).exists())

        # Test that the source page continues to exist in the source tree root (HomePage)
        # Test that the translated alias is no longer in the translated tree root (fr HomePage)
        self.assertNotIn(self.en_blog_post, en_root.get_descendants().specific())
        self.assertNotIn(self.fr_blog_post, fr_root.get_descendants().specific())
