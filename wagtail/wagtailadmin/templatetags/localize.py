from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils import formats
from django.utils.translation import get_language

register = template.Library()

# For reasons unkown, the el (greek) locale in django/conf/locale/el/formats.py 
# *did not* contain a DATE_INPUT_FORMATS -- so it fell back to using the US 
# date format (mm/dd/yy) which is not the correct one for Greece (dd/mm/yy). 
# This means that if we used a localized datepicker django *won't* be able to
# parse the dates! So a test here checks if DATE_INPUT_FORMATS is actually 
# defined in a format module. If yes then it will just return an empty string 
# so that the normal, localized date format from datepicker will be used.
# If DATE_INPUT_FORMATS is not defined then it will return
@register.assignment_tag
def get_date_format_override():
    if hasattr(settings, 'USE_I18N') and settings.USE_I18N==True:
        
        for m in formats.get_format_modules():
            if hasattr(m, 'DATE_INPUT_FORMATS'):
                return ''
            else: # fall back to the ISO to be sure date will be parsed
                return 'yy-mm-dd'
    else: # Fall back to ISO if I18N is *not* used
        return 'yy-mm-dd'

# This is a list of all supported langs for jquery-ui datepicker which exist in
# wagtailadmin/js/venor/i18n/. In case any new translations are added there the
# language code should also be added in this list.
SUPPORTED_DATEPICKER_LANGS = ['af', 'ar-DZ', 'ar', 'az', 'be', 'bg', 'bs', 'ca', 'cs', 'cy-GB', 'da', 'de',
    'el', 'en-AU', 'en-GB', 'en-NZ', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fo', 'fr-CA', 'fr-CH', 'fr', 'gl',
    'he', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka', 'kk', 'km', 'ko', 'ky', 'lb', 'lt', 'lv',
    'mk', 'ml', 'ms', 'nb', 'nl-BE', 'nl', 'nn', 'no', 'pl', 'pt-BR', 'pt', 'rm', 'ro', 'ru', 'sk', 'sl', 'sq',
    'sr-SR', 'sr', 'sv', 'ta', 'th', 'tj', 'tr', 'uk', 'vi', 'zh-CN', 'zh-HK', 'zh-TW'
]
# Get the correct i18n + l10n settings for datepicker depending on current 
# thread language  
@register.simple_tag
def get_localized_datepicker_js():
    if hasattr(settings, 'USE_I18N') and settings.USE_I18N==True and \
        hasattr(settings, 'USE_L10N') and settings.USE_L10N==True:
        
        lang  = get_language()
        
        if '-' in lang:
            lang_parts = lang.split('-')
            lang = lang_parts[0].lower() +'-'+ lang_parts[1].upper()
        else:
            lang=lang.lower()
        if lang in SUPPORTED_DATEPICKER_LANGS:
            translation_file = static("wagtailadmin/js/vendor/i18n/jquery.ui.datepicker-{0}.js".format(
                lang
            ))
            return '<script src="{0}"></script>'.format(translation_file)
        else: # Don't return anything if language is not supported
            return ''
        
    else: # Don't return anything if we don't use I18N and L10N
        return ''        
        