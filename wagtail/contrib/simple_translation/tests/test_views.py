from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.translation import gettext_lazy

from wagtail.contrib.simple_translation.forms import SubmitTranslationForm
from wagtail.contrib.simple_translation.models import after_create_page
from wagtail.contrib.simple_translation.views import (
    SubmitPageTranslationView, SubmitSnippetTranslationView, SubmitTranslationView)
from wagtail.core import hooks
from wagtail.core.models import Locale, Page, ParentNotTranslatedError
from wagtail.tests.i18n.models import TestPage
from wagtail.tests.snippets.models import TranslatableSnippet
from wagtail.tests.utils import TestCase, WagtailTestUtils


@override_settings(
    LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
)
class TestSubmitTranslationView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.first()
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.de_locale = Locale.objects.create(language_code="de")
        self.en_homepage = Page.objects.get(depth=2)
        self.factory = RequestFactory()

    def test_template_name(self):
        self.assertEqual(
            SubmitTranslationView.template_name,
            "simple_translation/admin/submit_translation.html",
        )

    def test_title(self):
        self.assertEqual(SubmitTranslationView().title, gettext_lazy("Translate"))
        self.assertEqual(SubmitTranslationView().get_title(), gettext_lazy("Translate"))

    def test_subtitle(self):
        view = SubmitTranslationView()
        view.object = self.en_homepage
        self.assertEqual(view.get_subtitle(), str(self.en_homepage))

    def test_get_form(self):
        view = SubmitTranslationView()
        view.request = self.factory.get("/path/does/not/matter/")
        view.object = self.en_homepage
        form = view.get_form()
        self.assertIsInstance(form, SubmitTranslationForm)

    def test_get_success_url(self):
        with self.assertRaises(NotImplementedError):
            view = SubmitTranslationView()
            view.object = self.en_homepage
            view.get_success_url()

    def test_get_context_data(self, **kwargs):
        view = SubmitTranslationView()
        view.request = self.factory.get("/path/does/not/matter/")
        view.object = self.en_homepage
        context = view.get_context_data()
        self.assertTrue("form" in context.keys())
        self.assertIsInstance(context["form"], SubmitTranslationForm)

    def test_dispatch_as_anon(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_homepage.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/admin/login/?next={url}")

    def test_dispatch_as_moderator(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_homepage.id,))
        user = self.login()
        group = Group.objects.get(name="Moderators")
        user.groups.add(group)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_dispatch_as_user_with_perm(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_homepage.id,))
        user = self.login()
        permission = Permission.objects.get(codename="submit_translation")
        user.user_permissions.add(permission)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


@override_settings(
    LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
)
class TestSubmitPageTranslationView(WagtailTestUtils, TestCase):
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

    def test_title(self):
        self.assertEqual(SubmitPageTranslationView.title, "Translate page")

    def test_get_subtitle(self):
        view = SubmitPageTranslationView()
        view.object = self.en_homepage
        self.assertEqual(view.get_subtitle(), "Welcome to your new Wagtail site!")

    def test_submit_page_translation_view_test_get(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_blog_index.id,))
        self.login()
        response = self.client.get(url)
        assert isinstance(response.context["form"], SubmitTranslationForm)

    def test_submit_page_translation_view_test_post_invalid(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_blog_index.id,))
        self.login()
        response = self.client.post(url, {})
        assert response.status_code == 200
        assert response.context["form"].errors == {"locales": ["This field is required."]}

    def test_submit_page_translation_view_test_post_single_locale(self):
        url = reverse("simple_translation:submit_page_translation", args=(self.en_blog_index.id,))
        de = Locale.objects.get(language_code="de").id
        data = {"locales": [de], "include_subtree": True}
        self.login()
        response = self.client.post(url, data)

        assert response.status_code == 302
        assert response.url == f"/admin/pages/{self.en_blog_index.get_parent().id}/"

        response = self.client.get(response.url)  # follow the redirect
        assert [msg.message for msg in response.context["messages"]] == [
            "The page 'Blog' was successfully created in German"
        ]

    def test_submit_page_translation_view_test_post_multiple_locales(self):
        # Needs an extra page to hit recursive function
        en_blog_post_sub = Page(title="Blog post sub", slug="blog-post-sub")
        self.en_blog_post.add_child(instance=en_blog_post_sub)

        url = reverse("simple_translation:submit_page_translation", args=(self.en_blog_post.id,))
        de = Locale.objects.get(language_code="de").id
        fr = Locale.objects.get(language_code="fr").id
        data = {"locales": [de, fr], "include_subtree": True}
        self.login()

        with self.assertRaisesMessage(ParentNotTranslatedError, ""):
            self.client.post(url, data)

        url = reverse("simple_translation:submit_page_translation", args=(self.en_blog_index.id,))
        response = self.client.post(url, data)

        assert response.status_code == 302
        assert response.url == f"/admin/pages/{self.en_blog_index.get_parent().id}/"

        response = self.client.get(response.url)  # follow the redirect
        assert [msg.message for msg in response.context["messages"]] == [
            "The page 'Blog' was successfully created in 2 locales"
        ]


@override_settings(
    LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
)
class TestSubmitSnippetTranslationView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.first()
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.en_snippet = TranslatableSnippet(text="Hello world", locale=self.en_locale)
        self.en_snippet.save()

    def test_get_title(self):
        view = SubmitSnippetTranslationView()
        view.object = self.en_snippet
        self.assertEqual(view.get_title(), "Translate translatable snippet")

    def test_get_object(self):
        view = SubmitSnippetTranslationView()
        view.object = self.en_snippet
        view.kwargs = {
            "app_label": "some_app",
            "model_name": "some_model",
            "pk": 1,
        }
        with self.assertRaises(Http404):
            view.get_object()

        content_type = ContentType.objects.get_for_model(self.en_snippet)
        view.kwargs = {
            "app_label": content_type.app_label,
            "model_name": content_type.model,
            "pk": str(self.en_snippet.pk),
        }
        self.assertEqual(view.get_object(), self.en_snippet)

    def test_get_success_url(self):
        view = SubmitSnippetTranslationView()
        view.object = self.en_snippet
        view.kwargs = {
            "app_label": "some_app",
            "model_name": "some_model",
            "pk": 99,
        }
        self.assertEqual(view.get_success_url(), "/admin/snippets/some_app/some_model/edit/99/")

    def test_get_success_message(self):
        view = SubmitSnippetTranslationView()
        view.object = self.en_snippet
        self.assertEqual(
            view.get_success_message(self.fr_locale),
            f"Successfully created French for translatable snippet 'TranslatableSnippet object ({self.en_snippet.id})'",
        )


@override_settings(
    LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("fr", "French"),
        ("de", "German"),
    ],
    WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True
)
class TestPageTreeSync(WagtailTestUtils, TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.first()
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.de_locale = Locale.objects.create(language_code="de")

        self.en_homepage = Page.objects.get(depth=2)
        self.fr_homepage = self.en_homepage.copy_for_translation(self.fr_locale)
        self.de_homepage = self.en_homepage.copy_for_translation(self.de_locale)

    def test_hook_function_registered(self):
        fns = hooks.get_hooks("after_create_page")

        self.assertIn(after_create_page, fns)

    def test_alias_created_after_page_saved(self):
        en_blog_index = TestPage(title="Blog", slug="blog")
        self.en_homepage.add_child(instance=en_blog_index)

        after_create_page(None, en_blog_index)

        fr_blog_index = en_blog_index.get_translation(self.fr_locale)
        de_blog_index = en_blog_index.get_translation(self.de_locale)

        self.assertEqual(fr_blog_index.alias_of.specific, en_blog_index)
        self.assertEqual(de_blog_index.alias_of.specific, en_blog_index)

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=False)
    def test_page_sync_disabled(self):
        en_blog_index = TestPage(title="Blog", slug="blog")
        self.en_homepage.add_child(instance=en_blog_index)

        after_create_page(None, en_blog_index)

        self.assertFalse(en_blog_index.has_translation(self.fr_locale))
        self.assertFalse(en_blog_index.has_translation(self.de_locale))
