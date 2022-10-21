from django.conf import settings
from django.urls import reverse

from wagtail.coreutils import get_supported_content_language_variant
from wagtail.models import Locale, TranslatableMixin


def get_locale_for(*, request=None, model=None, instance=None):
    """
    Helper to retrieve the locale to use depending on the context.
    If a locale is returned, it is annotated to indicate whether
    it's the default language when possible.
    """
    if not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        return

    if instance and not model:
        model = type(instance)

    if model and not issubclass(model, TranslatableMixin):
        return

    locales = Locale.objects.annotate_default_language()

    if instance:
        # Check if the instance's locale was already prefetched
        # and use it if so to avoid an additional query.
        field = model._meta.get_field("locale")
        if field.is_cached(instance):
            return instance.locale
        else:
            return locales.get(pk=instance.locale_id)

    selected_locale = request.GET.get("locale") if request is not None else None
    if selected_locale:
        try:
            return locales.get(language_code=selected_locale)
        except Locale.DoesNotExist:
            pass

    # Fall back to the default language
    return locales.get(
        language_code=get_supported_content_language_variant(settings.LANGUAGE_CODE)
    )


def is_default_locale(locale):
    """Determines whether the given locale is the current default."""
    # Use the `is_default_language` annotation if present.
    if hasattr(locale, "is_default_language"):
        return locale.is_default_language

    is_default_language = locale == Locale.get_default()

    # Set `is_default_language` for subsequent calls.
    setattr(locale, "is_default_language", is_default_language)
    return is_default_language


def add_locale_query_string(url, locale):
    if locale and not is_default_locale(locale):
        url += f"?locale={locale.language_code}"
    return url


def get_edit_setting_url(*args, locale=None):
    """
    Helper to retrieve the edit URL for a setting model.

    Edit URLs are in the following forms:
        - Generic settings: /app_name/model_name/
        - Site specific settings: /app_name/model_name/site_pk/
          where `site_pk` is the id of the site associated
          to a site-specific setting instance.

    When `locale` is set, a query string will be appended
    to the URL if the given locale isn't the default one.

    Usage:
        - Generic settings:
            `edit_url = get_edit_setting_url(app_name. model_name)`
        - Translatable generic settings:
            `edit_url = get_edit_setting_url(app_name. model_name, locale=locale)`
        - Site-specific settings:
            `edit_url = get_edit_setting_url(app_name. model_name, site_pk)`
        - Translatable site-specific settings:
            `edit_url = get_edit_setting_url(app_name. model_name, site_pk, locale=locale)`
    """

    return add_locale_query_string(reverse("wagtailsettings:edit", args=args), locale)
