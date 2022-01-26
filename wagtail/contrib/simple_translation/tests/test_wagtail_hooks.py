from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.admin import widgets as wagtailadmin_widgets
from wagtail.contrib.simple_translation.wagtail_hooks import (
    page_listing_more_buttons, register_submit_translation_permission)
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

        if get_user_model().USERNAME_FIELD == 'email':
            user = get_user_model().objects.create_user(email="jos@example.com")
        else:
            user = get_user_model().objects.create_user(username="jos")
        assert list(page_listing_more_buttons(root_page, self.PagePerms(user))) == []

        # No permissions, no button
        home_page = self.en_homepage
        assert list(page_listing_more_buttons(root_page, self.PagePerms(user))) == []

        # Homepage is translated to all languages, no button
        perm = Permission.objects.get(codename="submit_translation")

        if get_user_model().USERNAME_FIELD == 'email':
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
