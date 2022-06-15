from django.forms import Media, MediaDefiningClass

from wagtail import hooks
from wagtail.admin.ui.sidebar import LinkMenuItem as LinkMenuItemComponent
from wagtail.admin.ui.sidebar import SubMenuItem as SubMenuItemComponent
from wagtail.coreutils import cautious_slugify


class MenuItem(metaclass=MediaDefiningClass):
    def __init__(
        self, label, url, name=None, classnames="", icon_name="", attrs=None, order=1000
    ):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.icon_name = icon_name
        self.name = name or cautious_slugify(str(label))
        self.attrs = attrs
        self.order = order

    def is_shown(self, request):
        """
        Whether this menu item should be shown for the given request; permission
        checks etc should go here. By default, menu items are shown all the time
        """
        return True

    def is_active(self, request):
        return request.path.startswith(str(self.url))

    def render_component(self, request):
        return LinkMenuItemComponent(
            self.name,
            self.label,
            self.url,
            icon_name=self.icon_name,
            classnames=self.classnames,
            attrs=self.attrs,
        )


class Menu:
    def __init__(self, register_hook_name, construct_hook_name=None):
        self.register_hook_name = register_hook_name
        self.construct_hook_name = construct_hook_name
        # _registered_menu_items will be populated on first access to the
        # registered_menu_items property. We can't populate it in __init__ because
        # we can't rely on all hooks modules to have been imported at the point that
        # we create the admin_menu and settings_menu instances
        self._registered_menu_items = None

    @property
    def registered_menu_items(self):
        if self._registered_menu_items is None:
            self._registered_menu_items = [
                fn() for fn in hooks.get_hooks(self.register_hook_name)
            ]
        return self._registered_menu_items

    def menu_items_for_request(self, request):
        items = [item for item in self.registered_menu_items if item.is_shown(request)]

        # provide a hook for modifying the menu, if construct_hook_name has been set
        if self.construct_hook_name:
            for fn in hooks.get_hooks(self.construct_hook_name):
                fn(request, items)

        return items

    def active_menu_items(self, request):
        return [
            item
            for item in self.menu_items_for_request(request)
            if item.is_active(request)
        ]

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

    def is_active(self, request):
        return bool(self.menu.active_menu_items(request))

    def render_component(self, request):
        return SubMenuItemComponent(
            self.name,
            self.label,
            self.menu.render_component(request),
            icon_name=self.icon_name,
            classnames=self.classnames,
        )


class AdminOnlyMenuItem(MenuItem):
    """A MenuItem which is only shown to superusers"""

    def is_shown(self, request):
        return request.user.is_superuser


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
