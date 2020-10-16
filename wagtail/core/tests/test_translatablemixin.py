from unittest.mock import patch

from django.conf import settings
from django.core import checks
from django.test import TestCase

from wagtail.core.models import Locale
from wagtail.tests.i18n.models import InheritedTestModel, TestModel


def make_test_instance(model=None, **kwargs):
    if model is None:
        model = TestModel

    return model.objects.create(**kwargs)


class TestTranslatableMixin(TestCase):
    def setUp(self):
        language_codes = dict(settings.LANGUAGES).keys()

        for language_code in language_codes:
            Locale.objects.get_or_create(language_code=language_code)

        # create the locales
        self.locale = Locale.objects.get(language_code="en")
        self.another_locale = Locale.objects.get(language_code="fr")

        # add the main model
        self.main_instance = make_test_instance(
            locale=self.locale, title="Main Model"
        )

        # add a translated model
        self.translated_model = make_test_instance(
            locale=self.another_locale,
            translation_key=self.main_instance.translation_key,
            title="Translated Model",
        )

        # add a random model that shouldn't show up anywhere
        make_test_instance()

    def test_get_translations_inclusive_false(self):
        self.assertSequenceEqual(
            list(self.main_instance.get_translations()), [self.translated_model]
        )

    def test_get_translations_inclusive_true(self):
        self.assertEqual(
            list(self.main_instance.get_translations(inclusive=True)),
            [self.main_instance, self.translated_model],
        )

    def test_get_translation(self):
        self.assertEqual(
            self.main_instance.get_translation(self.locale), self.main_instance
        )

    def test_get_translation_using_locale_id(self):
        self.assertEqual(
            self.main_instance.get_translation(self.locale.id), self.main_instance
        )

    def test_get_translation_or_none_return_translation(self):
        with patch.object(
            self.main_instance, "get_translation"
        ) as mock_get_translation:
            mock_get_translation.return_value = self.translated_model
            self.assertEqual(
                self.main_instance.get_translation_or_none(self.another_locale),
                self.translated_model,
            )

    def test_get_translation_or_none_return_none(self):
        self.translated_model.delete()
        with patch.object(
            self.main_instance, "get_translation"
        ) as mock_get_translation:
            mock_get_translation.side_effect = self.main_instance.DoesNotExist
            self.assertEqual(
                self.main_instance.get_translation_or_none(self.another_locale), None
            )

    def test_has_translation_when_exists(self):
        self.assertTrue(self.main_instance.has_translation(self.locale))

    def test_has_translation_when_exists_using_locale_id(self):
        self.assertTrue(self.main_instance.has_translation(self.locale.id))

    def test_has_translation_when_none_exists(self):
        self.translated_model.delete()
        self.assertFalse(self.main_instance.has_translation(self.another_locale))

    def test_copy_for_translation(self):
        self.translated_model.delete()
        copy = self.main_instance.copy_for_translation(locale=self.another_locale)

        self.assertNotEqual(copy, self.main_instance)
        self.assertEqual(copy.translation_key, self.main_instance.translation_key)
        self.assertEqual(copy.locale, self.another_locale)
        self.assertEqual("Main Model", copy.title)

    def test_get_translation_model(self):
        self.assertEqual(self.main_instance.get_translation_model(), TestModel)

        # test with a model that inherits from `TestModel`
        inherited_model = make_test_instance(model=InheritedTestModel)
        self.assertEqual(inherited_model.get_translation_model(), TestModel)


class TestLocalized(TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.get()
        self.fr_locale = Locale.objects.create(language_code="fr")

        self.en_instance = make_test_instance(
            locale=self.en_locale, title="Main Model"
        )
        self.fr_instance = make_test_instance(
            locale=self.fr_locale, translation_key=self.en_instance.translation_key, title="Main Model"
        )

    def test_localized_same_language(self):
        # Shouldn't run an extra query if the instances locale matches the active language
        # FIXME: Cache active locale record so this is zero
        with self.assertNumQueries(1):
            instance = self.en_instance.localized

        self.assertEqual(instance, self.en_instance)

    def test_localized_different_language(self):
        with self.assertNumQueries(2):
            instance = self.fr_instance.localized

        self.assertEqual(instance, self.en_instance)


class TestSystemChecks(TestCase):
    def test_raises_error_if_unique_together_constraint_missing(self):
        previous_unique_together = TestModel._meta.unique_together
        try:
            TestModel._meta.unique_together = []
            errors = TestModel.check()
        finally:
            TestModel._meta.unique_together = previous_unique_together

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Error)
        self.assertEqual(errors[0].id, 'wagtailcore.E003')
