from django.conf import settings
from django.conf.locale import LANG_INFO
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import check_for_language, get_supported_language_variant


def get_content_languages():
    """
    Cache of settings.WAGTAIL_CONTENT_LANGUAGES in a dictionary for easy lookups by key.
    """
    content_languages = getattr(settings, "WAGTAIL_CONTENT_LANGUAGES", None)
    languages = dict(settings.LANGUAGES)

    if content_languages is None:
        # Default to a single language based on LANGUAGE_CODE
        default_language_code = get_supported_language_variant(settings.LANGUAGE_CODE)
        try:
            language_name = languages[default_language_code]
        except KeyError:
            # get_supported_language_variant on the 'null' translation backend (used for
            # USE_I18N=False) returns settings.LANGUAGE_CODE unchanged without accounting for
            # language variants (en-us versus en), so retry with the generic version.
            default_language_code = default_language_code.split("-")[0]
            try:
                language_name = languages[default_language_code]
            except KeyError:
                # Can't extract a display name, so fall back on displaying LANGUAGE_CODE instead
                language_name = settings.LANGUAGE_CODE
                # Also need to tweak the languages dict to get around the check below
                languages[default_language_code] = settings.LANGUAGE_CODE

        content_languages = [
            (default_language_code, language_name),
        ]

    # Check that each content language is in LANGUAGES
    for language_code, name in content_languages:
        if language_code not in languages:
            raise ImproperlyConfigured(
                "The language {} is specified in WAGTAIL_CONTENT_LANGUAGES but not LANGUAGES. "
                "WAGTAIL_CONTENT_LANGUAGES must be a subset of LANGUAGES.".format(
                    language_code
                )
            )

    return dict(content_languages)


def get_supported_content_language_variant(lang_code, strict=False):
    """
    Return the language code that's listed in supported languages, possibly
    selecting a more generic variant. Raise LookupError if nothing is found.
    If `strict` is False (the default), look for a country-specific variant
    when neither the language code nor its generic variant is found.
    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.

    This is equvilant to Django's `django.utils.translation.get_supported_content_language_variant`
    but reads the `WAGTAIL_CONTENT_LANGUAGES` setting instead.
    """
    if lang_code:
        # If 'fr-ca' is not supported, try special fallback or language-only 'fr'.
        possible_lang_codes = [lang_code]
        try:
            possible_lang_codes.extend(LANG_INFO[lang_code]["fallback"])
        except KeyError:
            pass
        generic_lang_code = lang_code.split("-")[0]
        possible_lang_codes.append(generic_lang_code)
        supported_lang_codes = get_content_languages()

        for code in possible_lang_codes:
            if code in supported_lang_codes and check_for_language(code):
                return code
        if not strict:
            # if fr-fr is not supported, try fr-ca.
            for supported_code in supported_lang_codes:
                if supported_code.startswith(generic_lang_code + "-"):
                    return supported_code
    raise LookupError(lang_code)


def get_locales_display_names() -> dict:
    """
    Cache of the locale id -> locale display name mapping
    """
    from wagtail.models import Locale  # inlined to avoid circular imports

    locales_map = {
        locale.pk: locale.get_display_name() for locale in Locale.objects.all()
    }
    return locales_map


def reset_cache(**kwargs):
    """
    Clear cache when global WAGTAIL_CONTENT_LANGUAGES/LANGUAGES/LANGUAGE_CODE settings are changed
    """
    if kwargs["setting"] in ("WAGTAIL_CONTENT_LANGUAGES", "LANGUAGES", "LANGUAGE_CODE"):
        get_content_languages.cache_clear()
        get_supported_content_language_variant.cache_clear()
