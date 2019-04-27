import inspect
import re
import unicodedata

from django.apps import apps
from django.conf import settings
from django.db.models import Model
from django.utils.encoding import force_text
from django.utils.functional import cached_property
from django.utils.text import slugify


WAGTAIL_APPEND_SLASH = getattr(settings, 'WAGTAIL_APPEND_SLASH', True)


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


def is_page_model(model):
    # module loaded before apps are ready
    from wagtail.core.models import Page

    if isinstance(model, Page):
        return True
    try:
        return issubclass(model, Page)
    except TypeError:
        return False


def get_content_type_for_model(model):
    """
    A wrapper for ContentType.objects.get_for_model() that applies the correct
    value for `for_concrete_model` depending on whether Wagtail supports proxy
    models for type of model supplied (currently only subclasses of `Page`).
    """
    # module loaded before apps are ready
    from django.contrib.contenttypes.models import ContentType
    return ContentType.objects.get_for_model(model, for_concrete_model=not is_page_model(model))


def get_content_types_for_models(*models):
    """
    A wrapper for ContentType.objects.get_for_models() that applies the correct
    value for `for_concrete_model` depending on whether Wagtail supports proxy
    models for type of model supplied (currently only subclasses of `Page`).
    """
    # module loaded before apps are ready
    from django.contrib.contenttypes.models import ContentType

    page_models = []
    other_models = []
    for model in models:
        if is_page_model(model):
            page_models.append(model)
        else:
            other_models.append(model)

    # Start with content types for page models
    content_types = ContentType.objects.get_for_models(*page_models, for_concrete_models=False)

    # Add content types for other models
    content_types.update(ContentType.objects.get_for_models(*other_models))

    return content_types


def transmute(obj, new_type):
    """
    Returns an object of type ``new_type`` using the attribute values
    from ``obj``. Typically used to 'upcast' a page model instance to
    more specific model instances without hitting the database.

    cached_property values are not copied, because the new type may
    have a separate implementation of the relevant method.
    """
    new_obj = new_type()
    for key, value in obj.__dict__.items():
        if not isinstance(value, cached_property):
            new_obj.__dict__[key] = value
    return new_obj
