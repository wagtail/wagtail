import inspect
import re
import unicodedata

from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.utils.encoding import force_str
from django.utils.text import slugify

from unidecode import unidecode

WAGTAIL_APPEND_SLASH = getattr(settings, 'WAGTAIL_APPEND_SLASH', True)


def camelcase_to_underscore(str):
    # https://djangosnippets.org/snippets/585/
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')


def string_to_ascii(value):
    """
    Convert a string to ascii.
    Note: Conversion relies on unidecode, to be replaced in a future release.
    Important: Consider AbstractFormField _migrate_legacy_clean_name before replcaing unidecode.
    """

    return str(unidecode(value))


def get_model_string(model):
    """
    Returns a string that can be used to identify the specified model.

    The format is: `app_label.ModelName`

    This an be reversed with the `resolve_model_string` function
    """
    return model._meta.app_label + '.' + model.__name__


def resolve_model_string(model_string, default_app=None):
    """
    Resolve an 'app_label.model_name' string into an actual model class.
    If a model class is passed in, just return that.

    Raises a LookupError if a model can not be found, or ValueError if passed
    something that is neither a model or a string.
    """
    if isinstance(model_string, str):
        try:
            app_label, model_name = model_string.split(".")
        except ValueError:
            if default_app is not None:
                # If we can't split, assume a model in current app
                app_label = default_app
                model_name = model_string
            else:
                raise ValueError("Can not resolve {0!r} into a model. Model names "
                                 "should be in the form app_label.model_name".format(
                                     model_string), model_string)

        return apps.get_model(app_label, model_name)

    elif isinstance(model_string, type) and issubclass(model_string, Model):
        return model_string

    else:
        raise ValueError("Can not resolve {0!r} into a model".format(model_string), model_string)


SCRIPT_RE = re.compile(r'<(-*)/script>')


def escape_script(text):
    """
    Escape `</script>` tags in 'text' so that it can be placed within a `<script>` block without
    accidentally closing it. A '-' character will be inserted for each time it is escaped:
    `<-/script>`, `<--/script>` etc.
    """
    return SCRIPT_RE.sub(r'<-\1/script>', text)


SLUGIFY_RE = re.compile(r'[^\w\s-]', re.UNICODE)


def cautious_slugify(value):
    """
    Convert a string to ASCII exactly as Django's slugify does, with the exception
    that any non-ASCII alphanumeric characters (that cannot be ASCIIfied under Unicode
    normalisation) are escaped into codes like 'u0421' instead of being deleted entirely.

    This ensures that the result of slugifying e.g. Cyrillic text will not be an empty
    string, and can thus be safely used as an identifier (albeit not a human-readable one).
    """
    value = force_str(value)

    # Normalize the string to decomposed unicode form. This causes accented Latin
    # characters to be split into 'base character' + 'accent modifier'; the latter will
    # be stripped out by the regexp, resulting in an ASCII-clean character that doesn't
    # need to be escaped
    value = unicodedata.normalize('NFKD', value)

    # Strip out characters that aren't letterlike, underscores or hyphens,
    # using the same regexp that slugify uses. This ensures that non-ASCII non-letters
    # (e.g. accent modifiers, fancy punctuation) get stripped rather than escaped
    value = SLUGIFY_RE.sub('', value)

    # Encode as ASCII, escaping non-ASCII characters with backslashreplace, then convert
    # back to a unicode string (which is what slugify expects)
    value = value.encode('ascii', 'backslashreplace').decode('ascii')

    # Pass to slugify to perform final conversion (whitespace stripping, applying
    # mark_safe); this will also strip out the backslashes from the 'backslashreplace'
    # conversion
    return slugify(value)


def safe_snake_case(value):
    """
    Convert a string to ASCII similar to Django's slugify, with catious handling of
    non-ASCII alphanumeric characters. See `cautious_slugify`.

    Any inner whitespace, hyphens or dashes will be converted to underscores and
    will be safe for Django template or filename usage.
    """

    slugified_ascii_string = cautious_slugify(value)

    snake_case_string = slugified_ascii_string.replace("-", "_")

    return snake_case_string


def accepts_kwarg(func, kwarg):
    """
    Determine whether the callable `func` has a signature that accepts the keyword argument `kwarg`
    """
    signature = inspect.signature(func)
    try:
        signature.bind_partial(**{kwarg: None})
        return True
    except TypeError:
        return False


class InvokeViaAttributeShortcut:
    """
    Used to create a shortcut that allows an object's named
    single-argument method to be invoked using a simple
    attribute reference syntax. For example, adding the
    following to an object:

    obj.page_url = InvokeViaAttributeShortcut(obj, 'get_page_url')

    Would allow you to invoke get_page_url() like so:

    obj.page_url.terms_and_conditions

    As well as the usual:

    obj.get_page_url('terms_and_conditions')
    """

    __slots__ = 'obj', 'method_name'

    def __init__(self, obj, method_name):
        self.obj = obj
        self.method_name = method_name

    def __getattr__(self, name):
        method = getattr(self.obj, self.method_name)
        return method(name)
