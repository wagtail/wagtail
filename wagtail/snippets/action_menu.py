"""Handles rendering of the list of actions in the footer of the snippet create/edit views."""

from functools import lru_cache

from django.contrib.admin.utils import quote
from django.forms import Media, MediaDefiningClass
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.core import hooks
from wagtail.snippets.permissions import get_permission_name


class ActionMenuItem(metaclass=MediaDefiningClass):
    """Defines an item in the actions drop-up on the snippet creation/edit view"""
    order = 100  # default order index if one is not specified on init
    template = 'wagtailsnippets/snippets/action_menu/menu_item.html'

    label = ''
    name = None
    classname = ''
    icon_name = ''

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def is_shown(self, request, context):
        """
        Whether this action should be shown on this request; permission checks etc should go here.

        request = the current request object

        context = dictionary containing at least:
            'view' = 'create' or 'edit'
            'model' = the model of the snippet being created/edited
            'instance' (if view = 'edit') = the snippet being edited
        """
        return True

    def get_context(self, request, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()
        context.update({
            'label': self.label,
            'url': self.get_url(request, context),
            'name': self.name,
            'classname': self.classname,
            'icon_name': self.icon_name,
        })
        return context

    def get_url(self, request, context):
        return None

    def render_html(self, request, parent_context):
        context = self.get_context(request, parent_context)
        return render_to_string(self.template, context, request=request)


class DeleteMenuItem(ActionMenuItem):
    name = 'action-delete'
    label = _("Delete")
    icon_name = 'bin'
    classname = 'action-secondary'

    def is_shown(self, request, context):
        delete_permission = get_permission_name('delete', context['model'])

        return (
            context['view'] == 'edit'
            and request.user.has_perm(delete_permission)
        )

    def get_url(self, request, context):
        return reverse('wagtailsnippets:delete', args=[
            context['model']._meta.app_label,
            context['model']._meta.model_name,
            quote(context['instance'].pk)
        ])


class SaveMenuItem(ActionMenuItem):
    name = 'action-save'
    label = _("Save")
    template = 'wagtailsnippets/snippets/action_menu/save.html'


@lru_cache(maxsize=None)
def get_base_snippet_action_menu_items(model):
    """
    Retrieve the global list of menu items for the snippet action menu,
    which may then be customised on a per-request basis
    """
    menu_items = [
        SaveMenuItem(order=0),
        DeleteMenuItem(order=10),
    ]

    for hook in hooks.get_hooks('register_snippet_action_menu_item'):
        menu_items.append(hook(model))

    return menu_items


class SnippetActionMenu:
    template = 'wagtailsnippets/snippets/action_menu/menu.html'

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        self.menu_items = []

        if 'instance' in self.context:
            self.context['model'] = self.context['instance'].__class__

        self.menu_items.extend([
            menu_item
            for menu_item in get_base_snippet_action_menu_items(self.context['model'])
            if menu_item.is_shown(self.request, self.context)
        ])

        self.menu_items.sort(key=lambda item: item.order)

        for hook in hooks.get_hooks('construct_snippet_action_menu'):
            hook(self.menu_items, self.request, self.context)

        try:
            self.default_item = self.menu_items.pop(0)
        except IndexError:
            self.default_item = None

    def render_html(self):
        return render_to_string(self.template, {
            'default_menu_item': self.default_item.render_html(self.request, self.context),
            'show_menu': bool(self.menu_items),
            'rendered_menu_items': [
                menu_item.render_html(self.request, self.context)
                for menu_item in self.menu_items
            ],
        }, request=self.request)

    @cached_property
    def media(self):
        media = Media()
        for item in self.menu_items:
            media += item.media
        return media
