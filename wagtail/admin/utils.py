from typing import TYPE_CHECKING, Any, Iterable, Tuple, Type, Union
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.module_loading import import_string

from wagtail.utils.decorators import cached_classmethod

if TYPE_CHECKING:
    from django.forms import Form

    from wagtail.admin.panels.group import ObjectList, TabbedInterface


def get_admin_base_url():
    """
    Gets the base URL for the wagtail admin site. This is set in `settings.WAGTAILADMIN_BASE_URL`.
    """
    return getattr(settings, "WAGTAILADMIN_BASE_URL", None)


def get_valid_next_url_from_request(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if not next_url or not url_has_allowed_host_and_scheme(
        url=next_url, allowed_hosts={request.get_host()}
    ):
        return ""
    return next_url


def get_latest_str(obj):
    """
    Helper function to get the latest string representation of an object.
    Draft changes are saved as revisions instead of immediately reflected to the
    instance, so this function utilises the latest revision's object_str
    attribute if available.
    """
    from wagtail.models import DraftStateMixin, Page

    if isinstance(obj, Page):
        return obj.specific_deferred.get_admin_display_title()
    if isinstance(obj, DraftStateMixin) and obj.latest_revision:
        return obj.latest_revision.object_str
    return str(obj)


def get_user_display_name(user):
    """
    Returns the preferred display name for the given user object: the result of
    user.get_full_name() if implemented and non-empty, or user.get_username() otherwise.
    """
    try:
        full_name = user.get_full_name().strip()
        if full_name:
            return full_name
    except AttributeError:
        pass

    try:
        return user.get_username()
    except AttributeError:
        # we were passed None or something else that isn't a valid user object; return
        # empty string to replicate the behaviour of {{ user.get_full_name|default:user.get_username }}
        return ""


def set_query_params(url: str, params: dict):
    """
    Given a URL and a dictionary of query parameters,
    returns a new URL with those query parameters added or updated.

    If the value of a query parameter is None, that parameter will be removed from the URL.
    """

    scheme, netloc, path, query, fragment = urlsplit(url)
    querydict = parse_qs(query)
    querydict.update(params)
    querydict = {key: value for key, value in querydict.items() if value is not None}
    query = urlencode(querydict, doseq=True)
    return urlunsplit((scheme, netloc, path, query, fragment))


class TabbedEditHandlerGeneratorMixin:
    # The class (or import path to one) that `get_edit_handler_class()` should
    # return by default.
    edit_handler_class: Union[str, Type] = "wagtail.admin.panels.TabbedInterface"

    # The class (or import path to one) that `get_edit_handler_tab_class()` should
    # return by default.
    edit_handler_tab_class: Union[str, Type] = "wagtail.admin.panels.ObjectList"

    # A Form class (or import path to one) that `create_edit_handler()` should provide
    # as `base_form_class` when creating the edit interface instance.
    base_form_class: Union[str, "Form"] = "wagtail.admin.forms.WagtailAdminModelForm"

    # An iterable of (`name`, `heading`) tuples for each tab to be included in the
    # edit interface for this model (when panels can be found).
    edit_handler_tabs: Iterable[Tuple[str, Any]] = []

    @staticmethod
    def _import_if_string(value: Union[str, Type]) -> Type:
        if isinstance(value, str):
            return import_string(value)
        return value

    @classmethod
    def get_edit_handler_class(cls) -> Type["TabbedInterface"]:
        """
        Return the class that `create_edit_handler()` should use to create the edit interface for
        this model. By default, the `edit_handler_class` class attribute value is used.
        """
        return cls._import_if_string(cls.edit_handler_class)

    @classmethod
    def get_edit_handler_tab_class(cls, tab_name: str = None) -> Type["ObjectList"]:
        """
        Returns the class that `create_edit_handler_tab()` should use to create tabs for the edit
        handler for this model. The name of the tab currently being created is provided as
        `tab_name` to allow subclasses to return a different value for specific tabs. By default,
        the `edit_handler_tab_class` class attribute value is used for all tabs.
        """
        return cls._import_if_string(cls.edit_handler_tab_class)

    @classmethod
    def get_base_form_class(cls) -> Type["Form"]:
        """
        Returns the form class that `create_edit_handler` should provide as `base_form_class` when
        creating the edit interface instance. By default, the `base_form_class` class attribute value
        is used.
        """
        return cls._import_if_string(cls.base_form_class)

    @classmethod
    def get_edit_handler_tabs(cls) -> Iterable[Tuple[str, Any]]:
        """
        Returns an iterable of tuples containing the `name` and `heading` values for each
        tab that `create_edit_hander_tabs()` should consider returning. By default, the
        `edit_handler_tabs` class attribute value is used.
        """
        return cls.edit_handler_tabs

    @cached_classmethod
    def get_edit_handler(cls) -> "TabbedInterface":
        """
        Returns a `TabbedInterface` instance that can be used for adding/editing instances of this
        model (bound to this class). By default, one is created by the `create_edit_handler()`
        class method.
        """
        if hasattr(cls, "edit_handler") and cls.edit_handler is not None:
            obj = cls.edit_handler
        else:
            obj = cls.create_edit_handler()

        return obj.bind_to_model(cls)

    @classmethod
    def create_edit_handler(cls) -> "TabbedInterface":
        """
        Creates and returns a `TabbedInterface` instance, using a number of dedicated methods and
        attribute values from this class.

        The return value type is determined by `get_edit_handler_class()`.

        The potential list of tabs included in the interface is determined by
        `get_edit_handler_tabs()`.

        The tabs themselves are created by `create_edit_hander_tabs()`.
        """
        _class = cls.get_edit_handler_class()
        return _class(
            list(cls.create_edit_hander_tabs()),
            base_form_class=cls.get_base_form_class(),
        )

    @classmethod
    def create_edit_hander_tabs(cls) -> Iterable["ObjectList"]:
        """
        Returns an iterable of `ObjectList` instances for each of the tabs to be included in the
        edit interface for this model. By default, the return value is determined by
        `get_edit_handler_tabs()` (usually the value of the model's `edit_handler_tabs`
        attribute), and whether panels can be found for them.

        Individual tabs are created by `create_edit_handler_tab()`.

        NOTE: Tabs for which no panels can be found (or where the list is empty) are not returned
        by default. Tabs can also be explicitly hidden for model classes by adding a
        `hide_{tab_name}_tab` class attribute with a value of `True`.
        """
        for name, heading in cls.get_edit_handler_tabs():
            # Allow subclasses to hide tabs without explicitly overridding
            # the attribute or method to return an empty list.
            if getattr(cls, f"hide_{name}_tab", False) is True:
                continue

            if tab := cls.create_edit_handler_tab(name, heading):
                yield tab

    @classmethod
    def create_edit_handler_tab(
        cls, name: str, heading: str
    ) -> Union["ObjectList", None]:
        """
        Returns an `ObjectList` instance matching the provided `name` and `heading` values, and
        a list of panels defined elsewhere on the model.

        The return type of the object is determined by `get_edit_handler_tab_class()` (usually the
        value of the model's `edit_handler_tab_class` attribute).

        To determine the panels that appear in the tab, the `name` value is used to find one of the
        following (in order of preference):

        1. A classmethod called `get_{name}_panels()`.
        2. A class attribute called `{name}_panels`.

        If neither of these attributes are found (or if one returns a falsey value), a value of
        `None` is returned, indicating that the tab should not be included in the edit interface.

        To hide a tab without explicitly overriding the relevant panel list method or attribute,
        you can add a `hide_{name}_tab` attribute to the class with a value of `True`.
        """
        _class = cls.get_edit_handler_tab_class(name)

        # Find panels to include in this tab
        if generator_method := getattr(cls, f"get_{name}_panels", None):
            # Prefer a method if one exists
            panels = list(generator_method())
        else:
            # Fall back to class attribute
            panels = list(getattr(cls, f"{name}_panels", []))

        if not panels:
            return None

        return _class(panels, heading=heading)
