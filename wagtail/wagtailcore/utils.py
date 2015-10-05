import re
import unicodedata

from django.db.models import Model
from django.apps import apps
from django.utils.encoding import force_text
from django.utils.text import slugify
from django.utils.six import string_types


def camelcase_to_underscore(str):
    # http://djangosnippets.org/snippets/585/
    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')


def resolve_model_string(model_string, default_app=None):
    """
    Resolve an 'app_label.model_name' string into an actual model class.
    If a model class is passed in, just return that.

    Raises a LookupError if a model can not be found, or ValueError if passed
    something that is neither a model or a string.
    """
    if isinstance(model_string, string_types):
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
    value = force_text(value)

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
