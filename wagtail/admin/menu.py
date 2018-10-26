from django.forms import Media, MediaDefiningClass
from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from django.utils.text import slugify

from wagtail.core import hooks


class MenuItem(metaclass=MediaDefiningClass):
    template = 'wagtailadmin/shared/menu_item.html'

    def __init__(self, label, url, name=None, classnames='', attrs=None, order=1000):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(str(label)))
        self.order = order

        if attrs:
            self.attr_string = flatatt(attrs)
        else:
            self.attr_string = ""

    def is_shown(self, request):
        """
        Whether this menu item should be shown for the given request; permission
        checks etc should go here. By default, menu items are shown all the time
        """
        return True

    def is_active(self, request):
        return request.path.startswith(str(self.url))

    def get_context(self, request):
        """Defines context for the template, overridable to use more data"""
        return {
            'name': self.name,
            'url': self.url,
            'classnames': self.classnames,
            'attr_string': self.attr_string,
            'label': self.label,
            'active': self.is_active(request)
        }

    def render_html(self, request):
        context = self.get_context(request)
        return render_to_string(self.template, context, request=request)


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
            self._registered_menu_items = [fn() for fn in hooks.get_hooks(self.register_hook_name)]
        return self._registered_menu_items

    def menu_items_for_request(self, request):
        return [item for item in self.registered_menu_items if item.is_shown(request)]

    def active_menu_items(self, request):
        return [item for item in self.menu_items_for_request(request) if item.is_active(request)]

    @property
    def media(self):
        media = Media()
        for item in self.registered_menu_items:
            media += item.media
        return media

    def render_html(self, request):
        menu_items = self.menu_items_for_request(request)

        # provide a hook for modifying the menu, if construct_hook_name has been set
        if self.construct_hook_name:
            for fn in hooks.get_hooks(self.construct_hook_name):
                fn(request, menu_items)

        rendered_menu_items = []
        for item in sorted(menu_items, key=lambda i: i.order):
            try:
                rendered_menu_items.append(item.render_html(request))
            except TypeError:
                # fallback for older render_html methods that don't accept a request arg
                rendered_menu_items.append(item.render_html(request))

        return mark_safe(''.join(rendered_menu_items))


class SubmenuMenuItem(MenuItem):
    template = 'wagtailadmin/shared/menu_submenu_item.html'

    """A MenuItem which wraps an inner Menu object"""
    def __init__(self, label, menu, **kwargs):
        self.menu = menu
        super().__init__(label, '#', **kwargs)

    @property
    def media(self):
        return Media(js=[static('wagtailadmin/js/submenu.js')]) + self.menu.media

    def is_shown(self, request):
        # show the submenu if one or more of its children is shown
        return bool(self.menu.menu_items_for_request(request))

    def is_active(self, request):
        return bool(self.menu.active_menu_items(request))

    def get_context(self, request):
        context = super().get_context(request)
        context['menu_html'] = self.menu.render_html(request)
        context['request'] = request
        return context


admin_menu = Menu(register_hook_name='register_admin_menu_item', construct_hook_name='construct_main_menu')
settings_menu = Menu(register_hook_name='register_settings_menu_item')
