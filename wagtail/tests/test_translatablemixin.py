from unittest.mock import patch

from django.conf import settings
from django.core import checks
from django.db import models
from django.test import TestCase, override_settings

from wagtail.models import Locale
from wagtail.test.i18n.models import (
    ClusterableTestModel,
    ClusterableTestModelChild,
    ClusterableTestModelTranslatableChild,
    InheritedTestModel,
    TestModel,
)


def make_test_instance(model=None, **kwargs):
    if model is None:
        model = TestModel

    return model.objects.create(**kwargs)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableMixin(TestCase):
    def setUp(self):
        language_codes = dict(settings.LANGUAGES).keys()

        for language_code in language_codes:
            Locale.objects.get_or_create(language_code=language_code)

        # create the locales
        self.locale = Locale.objects.get(language_code="en")
        self.another_locale = Locale.objects.get(language_code="fr")

        # add the main model
        self.main_instance = make_test_instance(locale=self.locale, title="Main Model")

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
            self.assertIsNone(
                self.main_instance.get_translation_or_none(self.another_locale)
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

    def test_copy_inherited_model_for_translation(self):
        instance = make_test_instance(model=InheritedTestModel)
        copy = instance.copy_for_translation(locale=self.another_locale)

        self.assertNotEqual(copy, instance)
        self.assertEqual(copy.translation_key, instance.translation_key)
        self.assertEqual(copy.locale, self.another_locale)

    def test_copy_clusterable_model_for_translation(self):
        instance = ClusterableTestModel.objects.create(
            title="A test clusterable model",
            children=[
                ClusterableTestModelChild(field="A non-translatable child object"),
            ],
            translatable_children=[
                ClusterableTestModelTranslatableChild(
                    field="A translatable child object"
                ),
            ],
        )

        copy = instance.copy_for_translation(locale=self.another_locale)

        instance_child = instance.children.get()
        copy_child = copy.children.get()
        instance_translatable_child = instance.translatable_children.get()
        copy_translatable_child = copy.translatable_children.get()

        self.assertNotEqual(copy, instance)
        self.assertEqual(copy.translation_key, instance.translation_key)
        self.assertEqual(copy.locale, self.another_locale)

        # Check children were copied
        self.assertNotEqual(copy_child, instance_child)
        self.assertEqual(copy_child.field, "A non-translatable child object")
        self.assertNotEqual(copy_translatable_child, instance_translatable_child)
        self.assertEqual(copy_translatable_child.field, "A translatable child object")

        # Check the translatable child's locale was updated but translation key is the same
        self.assertEqual(
            copy_translatable_child.translation_key,
            instance_translatable_child.translation_key,
        )
        self.assertEqual(copy_translatable_child.locale, self.another_locale)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocalized(TestCase):
    def setUp(self):
        self.en_locale = Locale.objects.get()
        self.fr_locale = Locale.objects.create(language_code="fr")

        self.en_instance = make_test_instance(locale=self.en_locale, title="Main Model")
        self.fr_instance = make_test_instance(
            locale=self.fr_locale,
            translation_key=self.en_instance.translation_key,
            title="Main Model",
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
    def test_unique_together_raises_no_error(self):
        # The default unique_together should not raise an error
        errors = TestModel.check()
        self.assertEqual(len(errors), 0)

    def test_unique_constraint_raises_no_error(self):
        # Allow replacing unique_together with UniqueConstraint
        # https://github.com/wagtail/wagtail/issues/11098
        previous_unique_together = TestModel._meta.unique_together
        try:
            TestModel._meta.unique_together = []
            TestModel._meta.constraints = [
                models.UniqueConstraint(
                    fields=["translation_key", "locale"],
                    name="unique_translation_key_locale_%(app_label)s_%(class)s",
                )
            ]
            errors = TestModel.check()

        finally:
            TestModel._meta.unique_together = previous_unique_together
            TestModel._meta.constraints = []

        self.assertEqual(len(errors), 0)

    def test_raises_error_if_both_unique_constraint_and_unique_together_are_missing(
        self,
    ):
        # The model has unique_together and not UniqueConstraint, remove
        # unique_together to trigger the error
        previous_unique_together = TestModel._meta.unique_together
        try:
            TestModel._meta.unique_together = []
            errors = TestModel.check()
        finally:
            TestModel._meta.unique_together = previous_unique_together

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Error)
        self.assertEqual(errors[0].id, "wagtailcore.E003")
        self.assertEqual(
            errors[0].msg,
            "i18n.TestModel is missing a UniqueConstraint for the fields: "
            "('translation_key', 'locale').",
        )
        self.assertEqual(
            errors[0].hint,
            "Add models.UniqueConstraint(fields=('translation_key', 'locale'), "
            "name='unique_translation_key_locale_i18n_testmodel') to "
            "TestModel.Meta.constraints.",
        )

    def test_error_with_both_unique_constraint_and_unique_together(self):
        # The model already has unique_together, add a UniqueConstraint
        # to trigger the error
        try:
            TestModel._meta.constraints = [
                models.UniqueConstraint(
                    fields=["translation_key", "locale"],
                    name="unique_translation_key_locale_%(app_label)s_%(class)s",
                )
            ]
            errors = TestModel.check()

        finally:
            TestModel._meta.constraints = []

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], checks.Error)
        self.assertEqual(errors[0].id, "wagtailcore.E003")
        self.assertEqual(
            errors[0].msg,
            "i18n.TestModel should not have both UniqueConstraint and unique_together for: "
            "('translation_key', 'locale').",
        )
        self.assertEqual(
            errors[0].hint,
            "Remove unique_together in favor of UniqueConstraint.",
        )
