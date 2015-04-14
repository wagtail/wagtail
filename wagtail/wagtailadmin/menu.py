from __future__ import unicode_literals

from six import text_type, with_metaclass

from django.forms import MediaDefiningClass, Media
from django.forms.utils import flatatt
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.template import Context, loader

from wagtail.wagtailcore import hooks


class MenuItem(with_metaclass(MediaDefiningClass)):

    def __init__(self, label, url, name=None, classnames='', attrs=None, order=1000, template='wagtailadmin/shared/menu_item.html'):
        self.label = label
        self.url = url
        self.classnames = classnames
        self.name = (name or slugify(text_type(label)))
        self.order = order
        self.template = template

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
        return request.path.startswith(self.url)

    def render_html(self, request):
        t = loader.get_template(self.template)
        c = Context({
            'name': self.name,
            'url': self.url,
            'classnames': self.classnames,
            'attr_string': self.attr_string,
            'label': self.label,
            'request': request,
            'active': self.is_active(request)
        })

        return t.render(c)


class Menu(object):
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

    def menu_items_active(self, request):
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
    """A MenuItem which wraps an inner Menu object"""
    def __init__(self, label, menu,
                 template='wagtailadmin/shared/menu_submenu_item.html',
                 **kwargs):
        self.menu = menu
        super(SubmenuMenuItem, self).__init__(label, '#', template=template, **kwargs)

    @property
    def media(self):
        return Media(js=['wagtailadmin/js/submenu.js']) + self.menu.media

    def is_shown(self, request):
        # show the submenu if one or more of its children is shown
        return bool(self.menu.menu_items_for_request(request))

    def is_active(self, request):
        return bool(self.menu.menu_items_active(request))

    def render_html(self, request):

        self.menu.menu_items_for_request(request)
        is_active = request.path.startswith(self.url)

        if not is_active:
            is_active = self.is_active(request)

        t = loader.get_template(self.template)
        c = Context({
            'name': self.name,
            'url': self.url,
            'classnames': self.classnames,
            'attr_string': self.attr_string,
            'label': self.label,
            'menu_html': self.menu.render_html(request),
            'request': request,
            'active': is_active
        })

        return t.render(c)


admin_menu = Menu(register_hook_name='register_admin_menu_item', construct_hook_name='construct_main_menu')
settings_menu = Menu(register_hook_name='register_settings_menu_item')
