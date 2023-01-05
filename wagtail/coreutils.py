import functools
import inspect
import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Any, Dict, Iterable, Union

from anyascii import anyascii
from django.apps import apps
from django.conf import settings
from django.conf.locale import LANG_INFO
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.signals import setting_changed
from django.db.models import Model
from django.db.models.base import ModelBase
from django.dispatch import receiver
from django.http import HttpRequest
from django.test import RequestFactory
from django.utils.encoding import force_str
from django.utils.text import capfirst, slugify
from django.utils.translation import check_for_language, get_supported_language_variant

if TYPE_CHECKING:
    from wagtail.models import Site

logger = logging.getLogger(__name__)

WAGTAIL_APPEND_SLASH = getattr(settings, "WAGTAIL_APPEND_SLASH", True)


def camelcase_to_underscore(str):
    # https://djangosnippets.org/snippets/585/
    return (
        re.sub("(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))", "_\\1", str).lower().strip("_")
    )


def string_to_ascii(value):
    """
    Convert a string to ascii.
    """

    return str(anyascii(value))


def get_model_string(model):
    """
    Returns a string that can be used to identify the specified model.

    The format is: `app_label.ModelName`

    This an be reversed with the `resolve_model_string` function
    """
    return model._meta.app_label + "." + model.__name__


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
                raise ValueError(
                    "Can not resolve {0!r} into a model. Model names "
                    "should be in the form app_label.model_name".format(model_string),
                    model_string,
                )

        return apps.get_model(app_label, model_name)

    elif isinstance(model_string, type) and issubclass(model_string, Model):
        return model_string

    else:
        raise ValueError(
            "Can not resolve {0!r} into a model".format(model_string), model_string
        )


SCRIPT_RE = re.compile(r"<(-*)/script>")


def escape_script(text):
    """
    Escape `</script>` tags in 'text' so that it can be placed within a `<script>` block without
    accidentally closing it. A '-' character will be inserted for each time it is escaped:
    `<-/script>`, `<--/script>` etc.
    """
    return SCRIPT_RE.sub(r"<-\1/script>", text)


SLUGIFY_RE = re.compile(r"[^\w\s-]", re.UNICODE)


def cautious_slugify(value):
    """
    Convert a string to ASCII exactly as Django's slugify does, with the exception
    that any non-ASCII alphanumeric characters (that cannot be ASCIIfied under Unicode
    normalisation) are escaped into codes like 'u0421' instead of being deleted entirely.

    This ensures that the result of slugifying (for example - Cyrillic) text will not be an empty
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
    # (accent modifiers, fancy punctuation) get stripped rather than escaped
    value = SLUGIFY_RE.sub("", value)

    # Encode as ASCII, escaping non-ASCII characters with backslashreplace, then convert
    # back to a unicode string (which is what slugify expects)
    value = value.encode("ascii", "backslashreplace").decode("ascii")

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


def get_content_type_label(content_type):
    """
    Return a human-readable label for a content type object, suitable for display in the admin
    in place of the default 'wagtailcore | page' representation
    """
    model = content_type.model_class()
    if model:
        return str(capfirst(model._meta.verbose_name))
    else:
        # no corresponding model class found; fall back on the name field of the ContentType
        return capfirst(content_type.model)


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

    __slots__ = "obj", "method_name"

    def __init__(self, obj, method_name):
        self.obj = obj
        self.method_name = method_name

    def __getattr__(self, name):
        method = getattr(self.obj, self.method_name)
        return method(name)

    def __getstate__(self):
        return {"obj": self.obj, "method_name": self.method_name}

    def __setstate__(self, state):
        self.obj = state["obj"]
        self.method_name = state["method_name"]


def find_available_slug(parent, requested_slug, ignore_page_id=None):
    """
    Finds an available slug within the specified parent.

    If the requested slug is not available, this adds a number on the end, for example:

     - 'requested-slug'
     - 'requested-slug-1'
     - 'requested-slug-2'

    And so on, until an available slug is found.

    The `ignore_page_id` keyword argument is useful for when you are updating a page,
    you can pass the page being updated here so the page's current slug is not
    treated as in use by another page.
    """
    pages = parent.get_children().filter(slug__startswith=requested_slug)

    if ignore_page_id:
        pages = pages.exclude(id=ignore_page_id)

    existing_slugs = set(pages.values_list("slug", flat=True))
    slug = requested_slug
    number = 1

    while slug in existing_slugs:
        slug = requested_slug + "-" + str(number)
        number += 1

    return slug


@functools.lru_cache()
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


@functools.lru_cache(maxsize=1000)
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


@functools.lru_cache()
def get_locales_display_names() -> dict:
    """
    Cache of the locale id -> locale display name mapping
    """
    from wagtail.models import Locale  # inlined to avoid circular imports

    locales_map = {
        locale.pk: locale.get_display_name() for locale in Locale.objects.all()
    }
    return locales_map


@receiver(setting_changed)
def reset_cache(**kwargs):
    """
    Clear cache when global WAGTAIL_CONTENT_LANGUAGES/LANGUAGES/LANGUAGE_CODE settings are changed
    """
    if kwargs["setting"] in ("WAGTAIL_CONTENT_LANGUAGES", "LANGUAGES", "LANGUAGE_CODE"):
        get_content_languages.cache_clear()
        get_supported_content_language_variant.cache_clear()


def multigetattr(item, accessor):
    """
    Like getattr, but accepts a dotted path as the accessor to be followed to any depth.
    At each step, the lookup on the object can be a dictionary lookup (foo['bar']) or an attribute
    lookup (foo.bar), and if it results in a callable, will be called (provided we can do so with
    no arguments, and it does not have an 'alters_data' property).

    Modelled on the variable resolution logic in Django templates:
    https://github.com/django/django/blob/f331eba6d576752dd79c4b37c41d981daa537fe6/django/template/base.py#L838
    """

    current = item

    for bit in accessor.split("."):
        try:  # dictionary lookup
            current = current[bit]
        # ValueError/IndexError are for numpy.array lookup on
        # numpy < 1.9 and 1.9+ respectively
        except (TypeError, AttributeError, KeyError, ValueError, IndexError):
            try:  # attribute lookup
                current = getattr(current, bit)
            except (TypeError, AttributeError):
                # Reraise if the exception was raised by a @property
                if bit in dir(current):
                    raise
                try:  # list-index lookup
                    current = current[int(bit)]
                except (
                    IndexError,  # list index out of range
                    ValueError,  # invalid literal for int()
                    KeyError,  # current is a dict without `int(bit)` key
                    TypeError,  # unsubscriptable object
                ):
                    raise AttributeError(
                        "Failed lookup for key [%s] in %r" % (bit, current)
                    )

        if callable(current):
            if getattr(current, "alters_data", False):
                raise SuspiciousOperation(
                    "Cannot call %r from multigetattr" % (current,)
                )

            # if calling without arguments is invalid, let the exception bubble up
            current = current()

    return current


def get_dummy_request(*, path: str = "/", site: "Site" = None) -> HttpRequest:
    """
    Return a simple ``HttpRequest`` instance that can be passed to
    ``Page.get_url()`` and other methods to benefit from improved performance
    when no real ``HttpRequest`` instance is available.

    If ``site`` is provided, the ``HttpRequest`` is made to look like it came
    from that Wagtail ``Site``.
    """
    server_port = 80
    if site:
        server_name = site.hostname
        server_port = site.port
    elif settings.ALLOWED_HOSTS == ["*"]:
        server_name = "example.com"
    else:
        server_name = settings.ALLOWED_HOSTS[0]

    # `SERVER_PORT` doesn't work when passed to the constructor
    return RequestFactory(SERVER_NAME=server_name).get(path, SERVER_PORT=server_port)


class BatchProcessor:
    """
    A class to help with processing of an unknown (and potentially very
    high) number of objects.

    Just set ``max_size`` to the maximum number of instances you want
    to be held in memory at any one time, and batches will be sent to the
    ``process()`` method as that number is reached, without you having to
    invoke ``process()`` regularly yourself. Just remember to invoke
    ``process()`` when you're done adding items, otherwise the final batch
    of objects will not be processed.
    """

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.items = []
        self.added_count = 0

    def __len__(self):
        return self.added_count

    def add(self, item: Any) -> None:
        self.items.append(item)
        self.added_count += 1
        if self.max_size and len(self.items) == self.max_size:
            self.process()

    def extend(self, iterable: Iterable[Any]) -> None:
        for item in iterable:
            self.add(item)

    def process(self):
        self.pre_process()
        self._do_processing()
        self.post_process()
        self.items.clear()

    def pre_process(self):
        """
        A hook to allow subclasses to do any pre-processing of the data
        before the ``process()`` method is called.
        """
        pass

    def _do_processing(self):
        """
        To be overridden by subclasses to do whatever it is
        that needs to be done to the items in ``self.items``.
        """
        raise NotImplementedError

    def post_process(self):
        """
        A hook to allow subclasses to do any post-processing
        after the ``process()`` method is called, and before
        ``self.items`` is cleared
        """
        pass


class BatchCreator(BatchProcessor):
    """
    A class to help with bulk creation of an unknown (and potentially very
    high) number of model instances.

    Just set ``max_size`` to the maximum number of instances you want
    to be held in memory at any one time, and batches of objects will
    be created as that number is reached, without you having to invoke
    the ``process()`` method regularly yourself. Just remember to
    invoke ``process()`` when you're done adding items, to ensure
    that the final batch items is saved.

    ``BatchSaver`` is migration-friendly! Just use the ``model``
    keyword argument when initializing to override the hardcoded model
    class with the version from your migration.
    """

    model: ModelBase = None

    def __init__(
        self, max_size: int, *, model: ModelBase = None, ignore_conflicts=False
    ):
        super().__init__(max_size)
        self.ignore_conflicts = ignore_conflicts
        self.created_count = 0
        if model is not None:
            self.model = model

    def initialize_instance(self, kwargs):
        return self.model(**kwargs)

    def add(self, *, instance: Model = None, **kwargs) -> None:
        if instance is None:
            instance = self.initialize_instance(kwargs)
        self.items.append(instance)
        self.added_count += 1
        if self.max_size and len(self.items) == self.max_size:
            self.process()

    def extend(self, iterable: Iterable[Union[Model, Dict[str, Any]]]) -> None:
        for value in iterable:
            if isinstance(value, self.model):
                self.add(instance=value)
            else:
                self.add(**value)

    def _do_processing(self):
        """
        Use bulk_create() to save ``self.items``.
        """
        if not self.items:
            return None
        self.created_count += len(
            self.model.objects.bulk_create(
                self.items, ignore_conflicts=self.ignore_conflicts
            )
        )

    def get_summary(self):
        opts = self.model._meta
        return f"{self.created_count}/{self.added_count} {opts.verbose_name_plural} were created successfully."
