import functools
import inspect
import logging
import re
import unicodedata
from typing import TYPE_CHECKING, Any, Dict, Iterable, Union

from anyascii import anyascii
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.signals import setting_changed
from django.db.models import Model
from django.db.models.base import ModelBase
from django.dispatch import receiver
from django.http import HttpRequest
from django.utils.encoding import force_str
from django.utils.text import slugify

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
        return model._meta.verbose_name.capitalize()
    else:
        # no corresponding model class found; fall back on the name field of the ContentType
        return content_type.model.capitalize()


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
@functools.lru_cache(maxsize=1000)
@functools.lru_cache()
@receiver(setting_changed)
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


def get_dummy_request(path: str = "/", site: "Site" = None) -> HttpRequest:
    """
    Return a simple ``HttpRequest`` instance that can be passed to
    ``Page.get_url()`` and other methods to benefit from improved performance
    when no real ``HttpRequest`` instance is available.

    If ``site`` is provided, the ``HttpRequest`` is made to look like it came
    from that Wagtail ``Site``.
    """
    request = HttpRequest()
    request.path = path
    request.method = "GET"
    SERVER_PORT = 80
    if site:
        SERVER_NAME = site.hostname
        SERVER_PORT = site.port
    elif settings.ALLOWED_HOSTS == ["*"]:
        SERVER_NAME = "example.com"
    else:
        SERVER_NAME = settings.ALLOWED_HOSTS[0]
    request.META = {"SERVER_NAME": SERVER_NAME, "SERVER_PORT": SERVER_PORT}
    return request


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
