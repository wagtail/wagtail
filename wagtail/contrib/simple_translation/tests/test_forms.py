from django.forms import CheckboxInput, HiddenInput
from django.test import TestCase, override_settings

from wagtail.contrib.simple_translation.forms import SubmitTranslationForm
from wagtail.core.models import Locale, Page
from wagtail.tests.i18n.models import TestPage
from wagtail.tests.utils import WagtailTestUtils


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
class TestSubmitPageTranslation(WagtailTestUtils, TestCase):
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

    def test_include_subtree(self):
        form = SubmitTranslationForm(instance=self.en_blog_post)
        self.assertIsInstance(form.fields["include_subtree"].widget, HiddenInput)

        form = SubmitTranslationForm(instance=self.en_blog_index)
        self.assertIsInstance(form.fields["include_subtree"].widget, CheckboxInput)
        self.assertEqual(
            form.fields["include_subtree"].label, "Include subtree (1 page)"
        )

        form = SubmitTranslationForm(instance=self.en_homepage)
        self.assertEqual(
            form.fields["include_subtree"].label, "Include subtree (2 pages)"
        )

    def test_locales_queryset(self):
        # Homepage is translated to all locales.
        form = SubmitTranslationForm(instance=self.en_homepage)
        self.assertEqual(
            list(
                form.fields["locales"].queryset.values_list("language_code", flat=True)
            ),
            [],
        )
        # Blog index can be translated to `de` and `fr`.
        form = SubmitTranslationForm(instance=self.en_blog_index)
        self.assertEqual(
            list(
                form.fields["locales"].queryset.values_list("language_code", flat=True)
            ),
            ["de", "fr"],
        )
        # Blog post can be translated to `de` and `fr`.
        form = SubmitTranslationForm(instance=self.en_blog_post)
        self.assertEqual(
            list(
                form.fields["locales"].queryset.values_list("language_code", flat=True)
            ),
            ["de", "fr"],
        )

    def test_select_all(self):
        form = SubmitTranslationForm(instance=self.en_homepage)
        # Homepage is translated to all locales.
        self.assertIsInstance(form.fields["select_all"].widget, HiddenInput)

        form = SubmitTranslationForm(instance=self.en_blog_index)
        # Blog post can be translated to `de` and `fr`.
        self.assertIsInstance(form.fields["select_all"].widget, CheckboxInput)
