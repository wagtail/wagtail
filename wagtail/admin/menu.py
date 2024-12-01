from warnings import warn

from django.core.exceptions import ImproperlyConfigured
from django.forms import Media, MediaDefiningClass
from django.utils.functional import cached_property

from wagtail import hooks
from wagtail.admin.ui.sidebar import LinkMenuItem as LinkMenuItemComponent
from wagtail.admin.ui.sidebar import SubMenuItem as SubMenuItemComponent
from wagtail.coreutils import cautious_slugify
from wagtail.utils.deprecation import RemovedInWagtail70Warning


class MenuItem(metaclass=MediaDefiningClass):
    def __init__(
        self,
        label,
        url,
        name=None,
        classname="",
        classnames="",
        icon_name="",
        attrs=None,
        order=1000,
    ):
        if classnames:
            warn(
                "The `classnames` kwarg for MenuItem is deprecated - use `classname` instead.",
                category=RemovedInWagtail70Warning,
            )
        self.label = label
        self.url = url
        self.classname = classname or classnames
        self.icon_name = icon_name
        self.name = name or cautious_slugify(str(label))
        self.attrs = attrs or {}
        self.order = order

    def is_shown(self, request):
        """
        Whether this menu item should be shown for the given request; permission
        checks etc should go here. By default, menu items are shown all the time
        """
        return True

    def render_component(self, request):
        return LinkMenuItemComponent(
            self.name,
            self.label,
            self.url,
            icon_name=self.icon_name,
            classname=self.classname,
            attrs=self.attrs,
        )


class DismissibleMenuItemMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["data-controller"] = "w-dismissible"
        self.attrs["data-w-dismissible-dismissed-class"] = "w-dismissible--dismissed"
        self.attrs["data-w-dismissible-id-value"] = self.name

    def render_component(self, request):
        profile = getattr(request.user, "wagtail_userprofile", None)

        # Menu item instances are cached, so make sure the existence of the
        # data-w-dismissible-dismissed-value attribute is correct for the user
        if profile and profile.dismissibles.get(self.name):
            self.attrs["data-w-dismissible-dismissed-value"] = "true"
        else:
            self.attrs.pop("data-w-dismissible-dismissed-value", None)

        return super().render_component(request)


class DismissibleMenuItem(DismissibleMenuItemMixin, MenuItem):
    pass


class Menu:
    def __init__(self, register_hook_name=None, construct_hook_name=None, items=None):
        if register_hook_name is not None and not isinstance(register_hook_name, str):
            raise ImproperlyConfigured(
                "Expected a string or None as register_hook_name, got %r. "
                "Did you mean to pass an `items` keyword argument instead?"
                % register_hook_name
            )

        self.register_hook_name = register_hook_name
        self.construct_hook_name = construct_hook_name
        self.initial_menu_items = items

    @cached_property
    def registered_menu_items(self):
        # Construct the list of menu items from the set passed to the constructor along with any
        # registered through hooks. We can't do this in __init__ because we can't rely on all hooks
        # modules to have been imported at the point that we create the admin_menu and
        # settings_menu instances
        if self.initial_menu_items:
            items = self.initial_menu_items.copy()
        else:
            items = []

        if self.register_hook_name:
            for fn in hooks.get_hooks(self.register_hook_name):
                items.append(fn())

        return items

    def menu_items_for_request(self, request):
        items = [item for item in self.registered_menu_items if item.is_shown(request)]

        # provide a hook for modifying the menu, if construct_hook_name has been set
        if self.construct_hook_name:
            for fn in hooks.get_hooks(self.construct_hook_name):
                fn(request, items)

        return items

    @property
    def media(self):
        media = Media()
        for item in self.registered_menu_items:
            media += item.media
        return media

    def render_component(self, request):
        menu_items = self.menu_items_for_request(request)
        rendered_menu_items = []
        for item in sorted(menu_items, key=lambda i: i.order):
            rendered_menu_items.append(item.render_component(request))
        return rendered_menu_items


class SubmenuMenuItem(MenuItem):
    """A MenuItem which wraps an inner Menu object"""

    def __init__(self, label, menu, **kwargs):
        self.menu = menu
        super().__init__(label, "#", **kwargs)

    def is_shown(self, request):
        # show the submenu if one or more of its children is shown
        return bool(self.menu.menu_items_for_request(request))

    def render_component(self, request):
        return SubMenuItemComponent(
            self.name,
            self.label,
            self.menu.render_component(request),
            icon_name=self.icon_name,
            classname=self.classname,
            attrs=self.attrs,
        )


class DismissibleSubmenuMenuItem(DismissibleMenuItemMixin, SubmenuMenuItem):
    pass


class AdminOnlyMenuItem(MenuItem):
    """A MenuItem which is only shown to superusers"""

    def is_shown(self, request):
        return request.user.is_superuser


class WagtailMenuRegisterable:
    #: The icon used for the menu item that appears in Wagtail's sidebar.
    menu_icon = ""

    #: The displayed label used for the menu item.
    menu_label = ""

    #: The ``name`` argument passed to the ``MenuItem`` constructor, becoming the ``name`` attribute value for that instance.
    #: This can be useful when manipulating the menu items in a custom menu hook, e.g. :ref:`construct_main_menu`.
    #: If unset, a slugified version of :attr:`menu_label` is used.
    menu_name = ""

    #: An integer determining the order of the menu item, 0 being the first place.
    #: By default, it will be the last item before Reports, whose order is 9000.
    menu_order = 8999

    #: The URL to be used for the menu item.
    menu_url = None

    #: Register the menu item within the admin's main menu.
    add_to_admin_menu = False

    #: Register the menu item within the admin's "Settings" menu.
    #: This takes precedence if both ``add_to_admin_menu`` and ``add_to_settings_menu`` are set to ``True``.
    add_to_settings_menu = False

    @cached_property
    def menu_item_class(self):
        """A ``wagtail.admin.menu.MenuItem`` subclass to be registered with a menu hook."""
        return type(
            f"{self.__class__.__name__}MenuItem",
            (MenuItem,),
            {},
        )

    def get_menu_item(self, order=None):
        """
        Returns a ``wagtail.admin.menu.MenuItem`` instance to be registered
        with the Wagtail admin.

        The ``order`` parameter allows the method to be called from the outside
        (e.g. a ``ViewSetGroup``) to create a sub menu item with
        the correct order.
        """
        return self.menu_item_class(
            label=self.menu_label,
            url=self.menu_url,
            name=self.menu_name,
            icon_name=self.menu_icon,
            order=order if order is not None else self.menu_order,
        )

    @cached_property
    def menu_hook(self):
        """
        The name of the hook to register the menu item within.

        This takes precedence over ``add_to_admin_menu`` and ``add_to_settings_menu``.
        """
        if self.add_to_settings_menu:
            return "register_settings_menu_item"
        if self.add_to_admin_menu:
            return "register_admin_menu_item"

    def register_menu_item(self):
        """Registers the menu item with the Wagtail admin."""
        if self.menu_hook:
            hooks.register(self.menu_hook, self.get_menu_item)


class WagtailMenuRegisterableGroup(WagtailMenuRegisterable):
    """
    A container for grouping together multiple WagtailMenuRegisterable instances.
    Creates a menu item with a submenu for accessing the main URL for each instances.
    """

    #: A list or tuple of ``WagtailMenuRegisterable`` classes or instances
    #: to be grouped together.
    items = ()

    menu_icon = "folder-open-inverse"
    add_to_admin_menu = True

    def __init__(self):
        """
        When initialising, instantiate the classes (or use the instances)
        within 'items', and assign the list to a ``registerables`` attribute.
        """
        self.registerables = [
            registerable() if callable(registerable) else registerable
            for registerable in self.items
        ]

    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for registerable in self.registerables:
            menu_items.append(registerable.get_menu_item(order=item_order))
            item_order += 1
        return menu_items

    def get_menu_item(self, order=None):
        return SubmenuMenuItem(
            label=self.menu_label,
            menu=Menu(items=self.get_submenu_items()),
            name=self.menu_name,
            icon_name=self.menu_icon,
            order=order if order is not None else self.menu_order,
        )


admin_menu = Menu(
    register_hook_name="register_admin_menu_item",
    construct_hook_name="construct_main_menu",
)
settings_menu = Menu(
    register_hook_name="register_settings_menu_item",
    construct_hook_name="construct_settings_menu",
)
reports_menu = Menu(
    register_hook_name="register_reports_menu_item",
    construct_hook_name="construct_reports_menu",
)
help_menu = Menu(
    register_hook_name="register_help_menu_item",
    construct_hook_name="construct_help_menu",
)
