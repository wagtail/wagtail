import functools

from django.conf import settings
from django.conf.locale import LANG_INFO
from django.core.exceptions import ImproperlyConfigured

from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.translation import check_for_language


# A setting that can be used in foreign key declarations
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
# Two additional settings that are useful in South migrations when
# specifying the user model in the FakeORM
try:
    AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME = AUTH_USER_MODEL.rsplit('.', 1)
except ValueError:
    raise ImproperlyConfigured("AUTH_USER_MODEL must be of the form"
                               " 'app_label.model_name'")


@functools.lru_cache()
def get_languages():
    """
    Cache of settings.LANGUAGES in a dictionary for easy lookups by key.
    """
    # TODO: Add support for WAGTAIL_LANGUAGES
    return dict(settings.LANGUAGES)


# Added in Django 2.1
@functools.lru_cache(maxsize=1000)
def get_supported_language_variant(lang_code, strict=False):
    """
    Return the language code that's listed in supported languages, possibly
    selecting a more generic variant. Raise LookupError if nothing is found.
    If `strict` is False (the default), look for a country-specific variant
    when neither the language code nor its generic variant is found.
    lru_cache should have a maxsize to prevent from memory exhaustion attacks,
    as the provided language codes are taken from the HTTP request. See also
    <https://www.djangoproject.com/weblog/2007/oct/26/security-fix/>.
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
        supported_lang_codes = get_languages()

        for code in possible_lang_codes:
            if code in supported_lang_codes and check_for_language(code):
                return code
        if not strict:
            # if fr-fr is not supported, try fr-ca.
            for supported_code in supported_lang_codes:
                if supported_code.startswith(generic_lang_code + "-"):
                    return supported_code
    raise LookupError(lang_code)


@receiver(setting_changed)
def reset_cache(**kwargs):
    """
    Clear cache when global LANGUAGES/LANGUAGE_CODE settings are changed
    """
    if kwargs["setting"] in ("LANGUAGES", "LANGUAGE_CODE"):
        get_languages.cache_clear()
        get_supported_language_variant.cache_clear()
