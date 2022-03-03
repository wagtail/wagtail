from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.contrib.simple_translation.wagtail_hooks import (
    page_listing_more_buttons,
    register_submit_translation_permission,
)
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


class TestMovingTranslatedPages(Utils):

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True, WAGTAIL_I18N_ENABLED=True)
    def test_move_translated_pages(self):
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        self.de_blog_index = self.en_blog_index.copy_for_translation(self.de_locale)

        # Create blog_post copies for translation
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)
        self.de_blog_post = self.en_blog_post.copy_for_translation(self.de_locale)

        # Confirm location of English blog post page before it is moved
        # Should be living at /blog/blog-post/ right now. But will eventually
        # exist at /blog-post/
        assert self.en_blog_post.get_parent().id == self.en_blog_index.id

        # Check if fr and de blog post parent ids are in the translated list
        # This is to make sure the fr blog_post is situated under /fr/blog/
        # (same concept with /de/).
        # We'll check these after the move to ensure they exist under /fr/ without
        # the /blog/ parent page.
        original_translated_parent_ids = [p.id for p in self.en_blog_index.get_translations()]
        assert self.fr_blog_post.get_parent().id in original_translated_parent_ids
        assert self.de_blog_post.get_parent().id in original_translated_parent_ids

        response = self.client.post(
            reverse("wagtailadmin_pages:move_confirm", args=(self.en_blog_post.id, self.en_homepage.id,)),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.fr_blog_post.refresh_from_db()
        self.de_blog_post.refresh_from_db()

        # Check if the new pages exist under their respective translated homepages
        home_page_translation_ids = [p.id for p in self.en_homepage.get_translations()]
        assert self.fr_blog_post.get_parent(update=True).id in home_page_translation_ids
        assert self.de_blog_post.get_parent(update=True).id in home_page_translation_ids

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=False)
    def test_unmovable_translation_pages(self):
        """
        Test trying to move a page when WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE
        is disabled.
        """
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        self.de_blog_index = self.en_blog_index.copy_for_translation(self.de_locale)

        # Create blog_post copies for translation
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)
        self.de_blog_post = self.en_blog_post.copy_for_translation(self.de_locale)

        # Confirm location of English blog post page before it is moved
        # Should be living at /blog/blog-post/ right now. But will eventually
        # exist at /blog-post/
        assert self.en_blog_post.get_parent().id == self.en_blog_index.id

        # Confirm the fr and de blog post pages are under the blog index page
        # We'll confirm these have not moved after ther POST request.
        original_translated_parent_ids = [p.id for p in self.en_blog_index.get_translations()]
        assert self.fr_blog_post.get_parent().id in original_translated_parent_ids
        assert self.de_blog_post.get_parent().id in original_translated_parent_ids

        response = self.client.post(
            reverse("wagtailadmin_pages:move_confirm", args=(self.en_blog_post.id, self.en_homepage.id,)),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        self.en_blog_post.refresh_from_db()
        self.fr_blog_post.refresh_from_db()
        self.de_blog_post.refresh_from_db()

        # Check that the en_blog_post page has moved directly under the home page.
        assert self.en_blog_post.get_parent(update=True).id == self.en_homepage.id

        # Check if the fr and de pages exist under their original parent page (/blog/)
        assert self.fr_blog_post.get_parent(update=True).id in original_translated_parent_ids
        assert self.de_blog_post.get_parent(update=True).id in original_translated_parent_ids

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True, WAGTAIL_I18N_ENABLED=True)
    def test_translation_count_in_context(self):
        """Test the number of `pages_to_move` is correct in the confirm_move.html template."""
        self.login()

        # BlogIndex needs translated pages before child pages can be translated
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)

        # Create blog_post copies for translation
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)

        response = self.client.get(
            reverse("wagtailadmin_pages:move_confirm", args=(self.en_blog_post.id, self.en_homepage.id,)),
            follow=True,
        )

        assert response.status_code == 200
        assert response.context['pages_to_move'] == 2
        assert f'This will also move 2 translations of this page and their child pages' in response.content.decode("utf-8")

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True, WAGTAIL_I18N_ENABLED=True)
    def test_divergent_translation_tree(self):
        """
        Test what happens when we try to move a translated/alias page that's diverged
        from it's mirrored tree.
        """
        self.login()

        self.en_new_parent = TestPage(title="Test Parent", slug="test-parent")
        self.en_homepage.add_child(instance=self.en_new_parent)

        # Copy the /blog/ and French /blog-post/ pages.
        self.fr_blog_index = self.en_blog_index.copy_for_translation(self.fr_locale)
        self.fr_blog_post = self.en_blog_post.copy_for_translation(self.fr_locale)
        # Copy the en new parent to be a french page
        self.fr_new_parent = self.en_new_parent.copy_for_translation(self.fr_locale)

        # Manually move the fr_blog_post to live under fr_new_parent
        action = MovePageAction(
            self.fr_blog_post,
            self.fr_new_parent,
            pos='last-child',
            user=None,
        )
        action.execute(skip_permission_checks=True)

        self.fr_blog_post.refresh_from_db()
        self.en_blog_post.refresh_from_db()

        # Confirm fr_blog_post parent id is the fr_new_parent id.
        # Confirm en_blog_post parent id is the en_blog_index id
        assert self.fr_blog_post.get_parent(update=True).id == self.fr_new_parent.id
        assert self.en_blog_post.get_parent(update=True).id == self.en_blog_index.id

        # Make a post request to move the en_blog_post to live under en_homepage
        response = self.client.post(
            reverse("wagtailadmin_pages:move_confirm", args=(self.en_blog_post.id, self.en_homepage.id,)),
            follow=True,
        )
        assert response.status_code == 200

        self.fr_blog_post.refresh_from_db()
        self.en_blog_post.refresh_from_db()

        # Confirm en_blog_posts parent id is en_homepage.id
        # Confirm that fr_blog_posts parent id is _still_ the fr_new_parent id
        assert self.en_blog_post.get_parent(update=True).id == self.en_homepage.id
        assert self.fr_blog_post.get_parent(update=True).id == self.fr_new_parent.id
