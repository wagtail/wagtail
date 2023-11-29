from unittest.mock import patch

from django.conf import settings
from django.core import checks
from django.db import models
from django.test import TestCase, override_settings
from django.utils import translation

from wagtail.models import Locale
from wagtail.models.i18n import TranslatableQuerySet
from wagtail.test.i18n.models import (
    ClusterableTestModel,
    ClusterableTestModelChild,
    ClusterableTestModelTranslatableChild,
    InheritedTestModel,
    TestDraftModel,
    TestModel,
)
from wagtail.test.utils import WagtailTestUtils


def make_test_instance(model=None, **kwargs):
    if model is None:
        model = TestModel

    return model.objects.create(**kwargs)


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestTranslatableQuerySetMixinLocalized(WagtailTestUtils, TestCase):
    """
    Test class for tests of the `localized` method of the `TranslatableQuerySetMixin`.

    These test rely on the `TestModel` inheriting from the `TranslatableMixin`.

    The `localized` method on the `TranslatableQuerySet` is the equivalent of the
    `localize` property on the `TranslatableMixin` but for a queryset instead of a
    single instance.

    "To localize" in this context means to convert a queryset of translatable objects
    into a queryset of the same length where each object is either the translated
    version  of the original object or the original object itself. The translation of
    interest is the one for active locale. If there is a translation for the active
    locale, the translated version is used, otherwise the original object is used.
    """

    example_model = TestModel
    draft_example_model = TestDraftModel

    @classmethod
    def create_en_instance(cls, model=None, **kwargs):
        model = model or cls.example_model
        return make_test_instance(model=model, locale=cls.locale_en, **kwargs)

    @classmethod
    def create_fr_translation(cls, instance, **kwargs):
        """
        Create a French translation for the given instance.

        This is achieved by creating a new instance with the same translation key as the
        given instance.
        """
        return instance.__class__.objects.create(
            locale=cls.locale_fr,
            translation_key=instance.translation_key,
            **kwargs,
        )

    @classmethod
    def setUpTestData(cls):
        cls.locale_en = Locale.objects.get(language_code="en")
        cls.locale_fr = Locale.objects.create(language_code="fr")

        # Create example instances with different titles for the locales simulating a
        # translation. Additionally, the titles differ between the locales so that
        # ordering by `title` leads to a different sort order between the locales.
        # Furthermore, the instances are created in an order so that their IDs should
        # not match the alphabetical ordering in either locale.
        cls.instance_CY_en = cls.create_en_instance(title="C")
        cls.instance_CY_fr = cls.create_fr_translation(cls.instance_CY_en, title="Y")

        cls.instance_AZ_en = cls.create_en_instance(title="A")
        cls.instance_AZ_fr = cls.create_fr_translation(cls.instance_AZ_en, title="Z")

        cls.instance_BX_en = cls.create_en_instance(title="B")
        cls.instance_BX_fr = cls.create_fr_translation(cls.instance_BX_en, title="X")

        # Create example instances with different draft and live states. This is to test
        # that the draft/live state of the translation is taken into account correctly.
        cls.instance_with_live_trans_en = cls.create_en_instance(
            model=cls.draft_example_model,
            title="Instance with live translation",
            live=True,
        )
        cls.instance_with_live_trans_fr = cls.create_fr_translation(
            cls.instance_with_live_trans_en,
            title="Live translation",
            live=True,
        )
        cls.instance_with_draft_trans_en = cls.create_en_instance(
            model=cls.draft_example_model,
            title="Instance with draft translation",
            live=True,
        )
        cls.instance_with_draft_trans_fr = cls.create_fr_translation(
            cls.instance_with_draft_trans_en,
            title="Draft translation",
            live=False,  # This makes the translation a draft.
        )

    def test_example_model_queryset_class(self):
        """Test that the example model uses the expected queryset class."""
        self.assertIsInstance(self.example_model.objects.all(), TranslatableQuerySet)

    def test_all_translated_all_in_queryset(self):
        """
        Test when all instances are translated and all instances are in the queryset.

        Localization in this situation could be achieved by returning all instances of
        the model in the active locale. All instances in the localized queryset are of
        the active locale.
        """
        queryset_en = self.example_model.objects.filter(locale=self.locale_en)
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            with self.assertNumQueries(2):
                queryset_localized = queryset_en.localized()
                # Call `repr` to evaluate the queryset.
                repr(queryset_localized)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
                self.instance_CY_fr,
            ],
            ordered=False,
        )

    def test_all_translated_subset_in_queryset(self):
        """
        Test when all instances are translated but only a subset of instances is in the
        queryset.

        Localization in this situation could be achieved by returning all instances of
        the model in the active locale and filtering for the translation keys in the
        original queryset. All instances in the localized queryset are of the active
        locale.
        """
        queryset_en = self.example_model.objects.filter(
            pk__in=[self.instance_AZ_en.id, self.instance_BX_en.id]
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            with self.assertNumQueries(2):
                queryset_localized = queryset_en.localized()
                # Call `repr` to evaluate the queryset.
                repr(queryset_localized)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
            ],
            ordered=False,
        )

    def test_subset_translated_all_in_queryset(self):
        """
        Test when a subset of instances is translated but all instances are in the
        queryset.

        This situation will need real localization where some instances in the localized
        queryset are of the active locale and some are not.
        """
        untranslated_instance = self.create_en_instance(title="Untranslated")
        queryset_en = self.example_model.objects.filter(locale=self.locale_en)
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
                untranslated_instance,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            with self.assertNumQueries(2):
                queryset_localized = queryset_en.localized()
                # Call `repr` to evaluate the queryset.
                repr(queryset_localized)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
                self.instance_CY_fr,
                untranslated_instance,
            ],
            ordered=False,
        )

    def test_subset_translated_subset_in_queryset_same_subsets(self):
        """
        Test when a subset of instances is translated and the same subset is in the
        queryset.

        This means that all translated instances are in the queryset. There is an
        untranslated instance, but it is not in the queryset.

        Localization in this situation could be achieved by returning all instances of
        the model in the active locale. All instances in the localized queryset are of
        the active locale.
        """
        untranslated_instance = self.create_en_instance(title="Untranslated")
        queryset_en = self.example_model.objects.filter(locale=self.locale_en).exclude(
            pk=untranslated_instance.id
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            with self.assertNumQueries(2):
                queryset_localized = queryset_en.localized()
                # Call `repr` to evaluate the queryset.
                repr(queryset_localized)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
                self.instance_CY_fr,
            ],
            ordered=False,
        )
        # Just being double explicit here.
        self.assertNotIn(untranslated_instance, queryset_localized)

    def test_subset_translated_subset_in_queryset_different_subsets(self):
        """
        Test when a subset of instances is translated and a different subset is in the
        queryset.

        This means that not all translated instances are in the queryset. Additionally,
        there is an untranslated instance and it is in the queryset.

        This situation will need real localization where some instances in the localized
        queryset are of the active locale and some are not.
        """
        untranslated_instance = self.create_en_instance(title="Untranslated")
        queryset_en = self.example_model.objects.filter(
            pk__in=[
                self.instance_AZ_en.id,
                self.instance_BX_en.id,
                untranslated_instance.id,
            ],
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                untranslated_instance,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            with self.assertNumQueries(2):
                queryset_localized = queryset_en.localized()
                # Call `repr` to evaluate the queryset.
                repr(queryset_localized)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
                untranslated_instance,
            ],
            ordered=False,
        )

    def test_original_queryset_ordered_by_title(self):
        """
        Test the effect of localization on the order of a queryset that is ordered by
        title.

        By default, the same ordering is applied. This does not mean that the order of
        the items is retained. Rather, the same fields are used for ordering. However,
        the ordering is likely to be different because the translated values are used.
        """
        queryset_en = self.example_model.objects.filter(locale=self.locale_en).order_by(
            "title"
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=True,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized()

        self.assertQuerysetEqual(
            queryset_localized,
            # These are ordered by the French titles.
            [
                self.instance_BX_fr,
                self.instance_CY_fr,
                self.instance_AZ_fr,
            ],
            ordered=True,
        )

    def test_explicitly_set_different_order_on_localized_queryset(self):
        """Test explicitly setting a different order on the localized queryset."""
        queryset_en = self.example_model.objects.filter(locale=self.locale_en).order_by(
            "id"
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_CY_en,
                self.instance_AZ_en,
                self.instance_BX_en,
            ],
            ordered=True,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized().order_by("title")

        self.assertQuerysetEqual(
            queryset_localized,
            # These are ordered by the French titles not their French IDs.
            [
                self.instance_BX_fr,
                self.instance_CY_fr,
                self.instance_AZ_fr,
            ],
            ordered=True,
        )

    def test_keep_order_of_original_queryset_via_argument(self):
        """Test keeping the order of the original queryset via an argument."""
        queryset_en = self.example_model.objects.filter(locale=self.locale_en).order_by(
            "title"
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=True,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized(keep_order=True)

        self.assertQuerysetEqual(
            queryset_localized,
            # These are still ordered by the English titles.
            [
                self.instance_AZ_fr,
                self.instance_BX_fr,
                self.instance_CY_fr,
            ],
            ordered=True,
        )

    def test_override_kept_order(self):
        """
        Test overriding the kept the order of the original queryset by explicitly
        ordering the localized queryset.

        Mostly a sanity check.
        """
        queryset_en = self.example_model.objects.filter(locale=self.locale_en).order_by(
            "title"
        )
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=True,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized(keep_order=True).order_by("id")

        self.assertQuerysetEqual(
            queryset_localized,
            # These are ordered by the French IDs not the English titles.
            [
                self.instance_CY_fr,
                self.instance_AZ_fr,
                self.instance_BX_fr,
            ],
            ordered=True,
        )

    def test_translation_is_draft(self):
        """
        Test when the translation is a draft.

        If a model can have a draft state, then a translation of an instance can exist
        but be in draft state. This case is tested here.

        This test is using the `TestDraftModel` model instead of the `TestModel` model.
        This is because the `TestDraftModel` model inherits from the `DraftStateMixin`
        and can be in a draft state.
        """
        queryset_en = self.draft_example_model.objects.filter(locale=self.locale_en)
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_with_live_trans_en,
                self.instance_with_draft_trans_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized()

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_with_live_trans_fr,
                # This is still the English instance because the French translation is
                # a draft.
                self.instance_with_draft_trans_en,
            ],
            ordered=False,
        )

    def test_include_draft_translations(self):
        """
        Test when the translation is a draft and `include_draft_translations=True` is
        passed.

        If a model can have a draft state, then a translation of an instance can exist
        but be in draft state. By default, translations that are "draft" are not used
        when localizing a queryset. In that case, the original instance is used instead.
        However, this behavior can be overridden by setting the
        `include_draft_translations` argument to `True`.

        This test is using the `TestDraftModel` model instead of the `TestModel` model.
        This is because the `TestDraftModel` model inherits from the `DraftStateMixin`
        and can be in a draft state.
        """
        queryset_en = self.draft_example_model.objects.filter(locale=self.locale_en)
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_with_live_trans_en,
                self.instance_with_draft_trans_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized(include_draft_translations=True)

        self.assertQuerysetEqual(
            queryset_localized,
            [
                self.instance_with_live_trans_fr,
                # This is included although it is draft.
                self.instance_with_draft_trans_fr,
            ],
            ordered=False,
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_localized_queryset_with_i18n_disabled(self):
        """Test method when i18n is disabled."""
        queryset_en = self.example_model.objects.filter(locale=self.locale_en)
        self.assertQuerysetEqual(
            queryset_en,
            [
                self.instance_AZ_en,
                self.instance_BX_en,
                self.instance_CY_en,
            ],
            ordered=False,
        )

        with translation.override("fr"):
            queryset_localized = queryset_en.localized()

        self.assertQuerysetEqual(queryset_localized, queryset_en, ordered=False)


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
