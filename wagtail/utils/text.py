import re
import unicodedata

from anyascii import anyascii
from django.utils.encoding import force_str
from django.utils.text import slugify

from wagtail.utils.coreutils import SCRIPT_RE

SCRIPT_RE = re.compile(r"<(-*)/script>")


def escape_script(text):
    """
    Escape `</script>` tags in 'text' so that it can be placed within a `<script>` block without
    accidentally closing it. A '-' character will be inserted for each time it is escaped:
    `<-/script>`, `<--/script>` etc.
    """
    return SCRIPT_RE.sub(r"<-\1/script>", text)


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
    value = unicodedata.normalize("NFKD", value)

    # Strip out characters that aren't letterlike, underscores or hyphens,
    # using the same regexp that slugify uses. This ensures that non-ASCII non-letters
    # (e.g. accent modifiers, fancy punctuation) get stripped rather than escaped
    value = SLUGIFY_RE.sub("", value)

    # Encode as ASCII, escaping non-ASCII characters with backslashreplace, then convert
    # back to a unicode string (which is what slugify expects)
    value = value.encode("ascii", "backslashreplace").decode("ascii")

    # Pass to slugify to perform final conversion (whitespace stripping, applying
    # mark_safe); this will also strip out the backslashes from the 'backslashreplace'
    # conversion
    return slugify(value)


SLUGIFY_RE = re.compile(r"[^\w\s-]", re.UNICODE)


def string_to_ascii(value):
    """
    Convert a string to ascii.
    """

    return str(anyascii(value))


def camelcase_to_underscore(str):
    # https://djangosnippets.org/snippets/585/
    return (
        re.sub("(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))", "_\\1", str).lower().strip("_")
    )
