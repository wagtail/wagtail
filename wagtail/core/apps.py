from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import formats, translation
from django.utils.translation import gettext_lazy as _


class WagtailCoreAppConfig(AppConfig):
    name = 'wagtail.core'
    label = 'wagtailcore'
    verbose_name = _("Wagtail core")

    def ready(self):
        from wagtail.core.signal_handlers import register_signal_handlers
        register_signal_handlers()

        # Update FORMAT_SETTINGS with Wagtail specific formats.
        # Now we can get localised WAGTAIL_* formats from custom format files.
        # https://docs.djangoproject.com/en/stable/topics/i18n/formatting/#creating-custom-format-files
        formats.FORMAT_SETTINGS = formats.FORMAT_SETTINGS.union([
            "WAGTAIL_DATE_FORMAT",
            "WAGTAIL_DATETIME_FORMAT",
            "WAGTAIL_TIME_FORMAT"
        ])

        # Check if WAGTAIL_* formats are compatible with Django input formats.
        if settings.USE_L10N:
            for code, label in settings.LANGUAGES:
                with translation.override(code):
                    for wagtail_format, django_formats in [
                        ("WAGTAIL_DATE_FORMAT", "DATE_INPUT_FORMATS"),
                        ("WAGTAIL_DATETIME_FORMAT", "DATETIME_INPUT_FORMATS"),
                        ("WAGTAIL_TIME_FORMAT", "TIME_INPUT_FORMATS"),
                    ]:
                        input_format = formats.get_format_lazy(wagtail_format)
                        input_formats = formats.get_format_lazy(django_formats)
                        print(code)
                        print(wagtail_format, input_format)
                        print(django_formats, [item for item in input_formats])
                        print("-")

                        if input_format not in input_formats:
                            raise ImproperlyConfigured(
                                f"{wagtail_format} {input_format} "
                                f"must be in {django_formats} for language {label} ({code})."
                            )
