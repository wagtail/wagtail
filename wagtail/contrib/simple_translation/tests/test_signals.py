from django.test import TestCase, override_settings

from wagtail.contrib.simple_translation.models import (
    create_translation_aliases_on_page_creation,
)
from wagtail.models import Locale, Page
from wagtail.test.i18n.models import TestPage
from wagtail.test.utils import WagtailTestUtils


class TestSimpleTranslationSignals(WagtailTestUtils, TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.first()
        self.fr_locale = Locale.objects.create(language_code="fr")

        # Ensure a clean state for homepages
        self.en_homepage = Page.objects.get(depth=2)

    def test_raw_save_does_not_create_alias(self):
        # Simulate fixture/raw save by calling the signal with raw=True
        import uuid

        page = TestPage(title="Raw Test", slug="raw-test")
        key = uuid.uuid4()
        page.translation_key = key
        # Call signal directly; should return early and not create alias
        create_translation_aliases_on_page_creation(Page, page, True, raw=True)

        self.assertFalse(Page.objects.filter(translation_key=key).exists())

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True)
    def test_parent_untranslated_no_alias_created(self):
        # Ensure parent's translations are removed
        Page.objects.filter(translation_key=self.en_homepage.translation_key).exclude(
            locale=self.en_locale
        ).delete()

        en_blog = TestPage(title="Blog", slug="blog-untranslated")
        self.en_homepage.add_child(instance=en_blog)

        # Simulate programmatic creation signal
        create_translation_aliases_on_page_creation(Page, en_blog, True)

        # There should be no French translation
        self.assertFalse(en_blog.has_translation(self.fr_locale))

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True)
    def test_parent_translated_alias_created(self):
        # Create translated homepage (and save it)
        self.fr_homepage = self.en_homepage.copy_for_translation(self.fr_locale)
        self.fr_homepage.save(clean=False)

        en_blog = TestPage(title="Blog", slug="blog-translated")
        self.en_homepage.add_child(instance=en_blog)

        # Simulate programmatic creation signal
        create_translation_aliases_on_page_creation(Page, en_blog, True)

        # Alias should be created automatically because parent is translated
        fr_blog = en_blog.get_translation(self.fr_locale)
        self.assertEqual(fr_blog.alias_of.specific, en_blog)

    @override_settings(WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE=True)
    def test_parent_translation_is_alias_still_creates_alias(self):
        """Regression: when the parent translated page is an alias, child aliases should still be created."""
        # Create the parent translation as an alias in the FR tree
        self.fr_homepage = self.en_homepage.copy_for_translation(
            self.fr_locale, alias=True
        )

        en_blog = TestPage(title="Blog", slug="blog-alias-parent")
        self.en_homepage.add_child(instance=en_blog)

        # Simulate programmatic creation signal
        create_translation_aliases_on_page_creation(Page, en_blog, True)

        # Alias should still be created under the aliased parent
        fr_blog = en_blog.get_translation(self.fr_locale)
        self.assertEqual(fr_blog.alias_of.specific, en_blog)
