import functools
import inspect
import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.http import HttpRequest

if TYPE_CHECKING:
    from wagtail.models import Site

logger = logging.getLogger(__name__)

WAGTAIL_APPEND_SLASH = getattr(settings, "WAGTAIL_APPEND_SLASH", True)


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
