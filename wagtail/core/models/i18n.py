import uuid

from django.apps import apps
from django.conf import settings
from django.core import checks
from django.db import migrations, models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import translation
from django.utils.encoding import force_str
from modelcluster.fields import ParentalKey

from wagtail.core.signals import pre_validate_delete
from wagtail.core.utils import get_content_languages, get_supported_content_language_variant

from .copying import _copy


def pk(obj):
    if isinstance(obj, models.Model):
        return obj.pk
    else:
        return obj


class LocaleManager(models.Manager):
    def get_for_language(self, language_code):
        """
        Gets a Locale from a language code.
        """
        return self.get(language_code=get_supported_content_language_variant(language_code))


class Locale(models.Model):
    #: The language code that represents this locale
    #:
    #: The language code can either be a language code on its own (such as ``en``, ``fr``),
    #: or it can include a region code (such as ``en-gb``, ``fr-fr``).
    language_code = models.CharField(max_length=100, unique=True)

    # Objects excludes any Locales that have been removed from LANGUAGES, This effectively disables them
    # The Locale management UI needs to be able to see these so we provide a separate manager `all_objects`
    objects = LocaleManager()
    all_objects = models.Manager()

    class Meta:
        ordering = [
            "language_code",
        ]

    @classmethod
    def get_default(cls):
        """
        Returns the default Locale based on the site's LANGUAGE_CODE setting
        """
        return cls.objects.get_for_language(settings.LANGUAGE_CODE)

    @classmethod
    def get_active(cls):
        """
        Returns the Locale that corresponds to the currently activated language in Django.
        """
        try:
            return cls.objects.get_for_language(translation.get_language())
        except (cls.DoesNotExist, LookupError):
            return cls.get_default()

    @transaction.atomic
    def delete(self, *args, **kwargs):
        # Provide a signal like pre_delete, but sent before on_delete validation.
        # This allows us to use the signal to fix up references to the locale to be deleted
        # that would otherwise fail validation.
        # Workaround for https://code.djangoproject.com/ticket/6870
        pre_validate_delete.send(sender=Locale, instance=self)
        return super().delete(*args, **kwargs)

    def language_code_is_valid(self):
        return self.language_code in get_content_languages()

    def get_display_name(self):
        return get_content_languages().get(self.language_code)

    def __str__(self):
        return force_str(self.get_display_name() or self.language_code)


class TranslatableMixin(models.Model):
    translation_key = models.UUIDField(default=uuid.uuid4, editable=False)
    locale = models.ForeignKey(Locale, on_delete=models.PROTECT, related_name="+", editable=False)

    class Meta:
        abstract = True
        unique_together = [("translation_key", "locale")]

    @classmethod
    def check(cls, **kwargs):
        errors = super(TranslatableMixin, cls).check(**kwargs)
        is_translation_model = cls.get_translation_model() is cls

        # Raise error if subclass has removed the unique_together constraint
        # No need to check this on multi-table-inheritance children though as it only needs to be applied to
        # the table that has the translation_key/locale fields
        if is_translation_model and ("translation_key", "locale") not in cls._meta.unique_together:
            errors.append(
                checks.Error(
                    "{0}.{1} is missing a unique_together constraint for the translation key and locale fields"
                    .format(cls._meta.app_label, cls.__name__),
                    hint="Add ('translation_key', 'locale') to {}.Meta.unique_together".format(cls.__name__),
                    obj=cls,
                    id='wagtailcore.E003',
                )
            )

        return errors

    @property
    def localized(self):
        """
        Finds the translation in the current active language.

        If there is no translation in the active language, self is returned.
        """
        try:
            locale = Locale.get_active()
        except (LookupError, Locale.DoesNotExist):
            return self

        if locale.id == self.locale_id:
            return self

        return self.get_translation_or_none(locale) or self

    def get_translations(self, inclusive=False):
        """
        Returns a queryset containing the translations of this instance.
        """
        translations = self.__class__.objects.filter(
            translation_key=self.translation_key
        )

        if inclusive is False:
            translations = translations.exclude(id=self.id)

        return translations

    def get_translation(self, locale):
        """
        Finds the translation in the specified locale.

        If there is no translation in that locale, this raises a ``model.DoesNotExist`` exception.
        """
        return self.get_translations(inclusive=True).get(locale_id=pk(locale))

    def get_translation_or_none(self, locale):
        """
        Finds the translation in the specified locale.

        If there is no translation in that locale, this returns None.
        """
        try:
            return self.get_translation(locale)
        except self.__class__.DoesNotExist:
            return None

    def has_translation(self, locale):
        """
        Returns True if a translation exists in the specified locale.
        """
        return self.get_translations(inclusive=True).filter(locale_id=pk(locale)).exists()

    def copy_for_translation(self, locale):
        """
        Creates a copy of this instance with the specified locale.

        Note that the copy is initially unsaved.
        """
        translated, child_object_map = _copy(self)
        translated.locale = locale

        # Update locale on any translatable child objects as well
        # Note: If this is not a subclass of ClusterableModel, child_object_map will always be '{}'
        for (child_relation, old_pk), child_object in child_object_map.items():
            if isinstance(child_object, TranslatableMixin):
                child_object.locale = locale

        return translated

    def get_default_locale(self):
        """
        Finds the default locale to use for this object.

        This will be called just before the initial save.
        """
        # Check if the object has any parental keys to another translatable model
        # If so, take the locale from the object referenced in that parental key
        parental_keys = [
            field
            for field in self._meta.get_fields()
            if isinstance(field, ParentalKey)
            and issubclass(field.related_model, TranslatableMixin)
        ]

        if parental_keys:
            parent_id = parental_keys[0].value_from_object(self)
            return (
                parental_keys[0]
                .related_model.objects.defer().select_related("locale")
                .get(id=parent_id)
                .locale
            )

        return Locale.get_default()

    @classmethod
    def get_translation_model(cls):
        """
        Returns this model's "Translation model".

        The "Translation model" is the model that has the ``locale`` and
        ``translation_key`` fields.
        Typically this would be the current model, but it may be a
        super-class if multi-table inheritance is in use (as is the case
        for ``wagtailcore.Page``).
        """
        return cls._meta.get_field("locale").model


def bootstrap_translatable_model(model, locale):
    """
    This function populates the "translation_key", and "locale" fields on model instances that were created
    before wagtail-localize was added to the site.

    This can be called from a data migration, or instead you could use the "boostrap_translatable_models"
    management command.
    """
    for instance in (
        model.objects.filter(translation_key__isnull=True).defer().iterator()
    ):
        instance.translation_key = uuid.uuid4()
        instance.locale = locale
        instance.save(update_fields=["translation_key", "locale"])


class BootstrapTranslatableModel(migrations.RunPython):
    def __init__(self, model_string, language_code=None):
        if language_code is None:
            language_code = get_supported_content_language_variant(settings.LANGUAGE_CODE)

        def forwards(apps, schema_editor):
            model = apps.get_model(model_string)
            Locale = apps.get_model("wagtailcore.Locale")

            locale = Locale.objects.get(language_code=language_code)
            bootstrap_translatable_model(model, locale)

        def backwards(apps, schema_editor):
            pass

        super().__init__(forwards, backwards)


class BootstrapTranslatableMixin(TranslatableMixin):
    """
    A version of TranslatableMixin without uniqueness constraints.

    This is to make it easy to transition existing models to being translatable.

    The process is as follows:
     - Add BootstrapTranslatableMixin to the model
     - Run makemigrations
     - Create a data migration for each app, then use the BootstrapTranslatableModel operation in
       wagtail.core.models on each model in that app
     - Change BootstrapTranslatableMixin to TranslatableMixin
     - Run makemigrations again
     - Migrate!
    """
    translation_key = models.UUIDField(null=True, editable=False)
    locale = models.ForeignKey(
        Locale, on_delete=models.PROTECT, null=True, related_name="+", editable=False
    )

    @classmethod
    def check(cls, **kwargs):
        # skip the check in TranslatableMixin that enforces the unique-together constraint
        return super(TranslatableMixin, cls).check(**kwargs)

    class Meta:
        abstract = True


def get_translatable_models(include_subclasses=False):
    """
    Returns a list of all concrete models that inherit from TranslatableMixin.
    By default, this only includes models that are direct children of TranslatableMixin,
    to get all models, set the include_subclasses attribute to True.
    """
    translatable_models = [
        model
        for model in apps.get_models()
        if issubclass(model, TranslatableMixin) and not model._meta.abstract
    ]

    if include_subclasses is False:
        # Exclude models that inherit from another translatable model
        root_translatable_models = set()

        for model in translatable_models:
            root_translatable_models.add(model.get_translation_model())

        translatable_models = [
            model for model in translatable_models if model in root_translatable_models
        ]

    return translatable_models


@receiver(pre_save)
def set_locale_on_new_instance(sender, instance, **kwargs):
    if not isinstance(instance, TranslatableMixin):
        return

    if instance.locale_id is not None:
        return

    # If this is a fixture load, use the global default Locale
    # as the page tree is probably in an flux
    if kwargs["raw"]:
        instance.locale = Locale.get_default()
        return

    instance.locale = instance.get_default_locale()
