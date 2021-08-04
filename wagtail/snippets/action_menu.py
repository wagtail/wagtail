"""Handles rendering of the list of actions in the footer of the snippet create/edit views."""
import inspect

from functools import lru_cache
from warnings import warn

from django.contrib.admin.utils import quote
from django.forms import Media
from django.template.loader import get_template, render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.ui.components import Component
from wagtail.core import hooks
from wagtail.snippets.permissions import get_permission_name
from wagtail.utils.deprecation import RemovedInWagtail217Warning


def requires_request_arg(method):
    """
    Helper function to handle deprecation of old ActionMenuItem API where get_url, is_show,
    get_context and render_html all accepted both 'request' and 'parent_context' as arguments
    """
    try:
        # see if this is a pre-2.15 get_url method that takes both request and context kwargs
        inspect.signature(method).bind({})
    except TypeError:
        return True
    else:
        return False


class ActionMenuItem(Component):
    """Defines an item in the actions drop-up on the snippet creation/edit view"""
    order = 100  # default order index if one is not specified on init
    template_name = 'wagtailsnippets/snippets/action_menu/menu_item.html'
    template = None  # RemovedInWagtail217Warning

    label = ''
    name = None
    classname = ''
    icon_name = ''

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def is_shown(self, *args):
        # accepts both is_shown(request, context) (pre-2.15 signature)
        # and is_shown(context) (signature as of 2.15)
        # to allow for pre-2.15 ActionMenuItem subclasses calling super().
        # RemovedInWagtail217Warning: signature should become is_shown(self, context)
        """
        Whether this action should be shown on this request; permission checks etc should go here.

        request = the current request object

        context = dictionary containing at least:
            'view' = 'create' or 'edit'
            'model' = the model of the snippet being created/edited
            'instance' (if view = 'edit') = the snippet being edited
        """
        if len(args) == 2:
            warn(
                "ActionMenuItem.is_shown no longer takes a 'request' argument. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15",
                category=RemovedInWagtail217Warning, stacklevel=2
            )
        return True

    def get_context(self, request, parent_context):
        # Obsolete - included here for pre-2.15 subclasses that override this and call super().
        # RemovedInWagtail217Warning
        return self.get_context_data(parent_context)

    get_context.is_base_method = True

    def get_context_data(self, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()

        if requires_request_arg(self.get_url):
            warn(
                "%s.get_url should no longer take a 'request' argument. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(self).__name__,
                category=RemovedInWagtail217Warning
            )
            url = self.get_url(parent_context['request'], parent_context)
        else:
            url = self.get_url(parent_context)

        context.update({
            'label': self.label,
            'url': url,
            'name': self.name,
            'classname': self.classname,
            'icon_name': self.icon_name,
            'request': parent_context['request'],
        })
        return context

    def get_url(self, *args):
        # accepts both get_url(request, parent_context) (pre-2.15 signature)
        # and get_url(parent_context) (signature as of 2.15)
        # to allow for pre-2.15 ActionMenuItem subclasses calling super().
        # RemovedInWagtail217Warning: signature should become get_url(self, parent_context)
        return None

    def render_html(self, *args):
        # accepts both render_html(request, parent_context) (pre-2.15 signature)
        # and render_html(parent_context) (signature as of 2.15)
        # to allow for pre-2.15 ActionMenuItem subclasses calling super().
        # RemovedInWagtail217Warning: signature should become render_html(self, parent_context)

        if len(args) == 2:
            warn(
                "ActionMenuItem.render_html no longer takes a 'request' argument. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15",
                category=RemovedInWagtail217Warning, stacklevel=2
            )
            request, parent_context = args
        else:
            parent_context, = args

        if not getattr(self.get_context, 'is_base_method', False):
            # get_context has been overridden, so call it instead of get_context_data
            warn(
                "%s should define get_context_data(self, parent_context) instead of get_context(self, request, get_context_data). "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(self).__name__,
                category=RemovedInWagtail217Warning
            )
            context_data = self.get_context(parent_context['request'], parent_context)
        else:
            context_data = self.get_context_data(parent_context)

        if self.template:
            warn(
                "%s should define template_name instead of template."
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(self).__name__,
                category=RemovedInWagtail217Warning
            )
            template_name = self.template
        else:
            template_name = self.template_name

        template = get_template(template_name)
        return template.render(context_data)


class DeleteMenuItem(ActionMenuItem):
    name = 'action-delete'
    label = _("Delete")
    icon_name = 'bin'
    classname = 'action-secondary'

    def is_shown(self, context):
        delete_permission = get_permission_name('delete', context['model'])

        return (
            context['view'] == 'edit'
            and context['request'].user.has_perm(delete_permission)
        )

    def get_url(self, context):
        return reverse('wagtailsnippets:delete', args=[
            context['model']._meta.app_label,
            context['model']._meta.model_name,
            quote(context['instance'].pk)
        ])


class SaveMenuItem(ActionMenuItem):
    name = 'action-save'
    label = _("Save")
    template_name = 'wagtailsnippets/snippets/action_menu/save.html'


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
        action_menu_item = hook(model)
        if action_menu_item:
            menu_items.append(action_menu_item)

    return menu_items


class SnippetActionMenu:
    template = 'wagtailsnippets/snippets/action_menu/menu.html'

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        self.context['request'] = request
        self.menu_items = []

        if 'instance' in self.context:
            self.context['model'] = self.context['instance'].__class__

        for menu_item in get_base_snippet_action_menu_items(self.context['model']):
            if requires_request_arg(menu_item.is_shown):
                warn(
                    "%s.is_shown should no longer take a 'request' argument. "
                    "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(menu_item).__name__,
                    category=RemovedInWagtail217Warning
                )
                is_shown = menu_item.is_shown(self.request, self.context)
            else:
                is_shown = menu_item.is_shown(self.context)

            if is_shown:
                self.menu_items.append(menu_item)

        self.menu_items.sort(key=lambda item: item.order)

        for hook in hooks.get_hooks('construct_snippet_action_menu'):
            hook(self.menu_items, self.request, self.context)

        try:
            self.default_item = self.menu_items.pop(0)
        except IndexError:
            self.default_item = None

    def render_html(self):
        rendered_menu_items = []
        for menu_item in self.menu_items:
            if requires_request_arg(menu_item.render_html):
                warn(
                    "%s.render_html should no longer take a 'request' argument. "
                    "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(menu_item).__name__,
                    category=RemovedInWagtail217Warning
                )
                rendered_menu_items.append(menu_item.render_html(self.request, self.context))
            else:
                rendered_menu_items.append(menu_item.render_html(self.context))

        if requires_request_arg(self.default_item.render_html):
            warn(
                "%s.render_html should no longer take a 'request' argument. "
                "See https://docs.wagtail.io/en/stable/releases/2.15.html#template-components-2-15" % type(self.default_item).__name__,
                category=RemovedInWagtail217Warning
            )
            rendered_default_item = self.default_item.render_html(self.request, self.context)
        else:
            rendered_default_item = self.default_item.render_html(self.context)

        return render_to_string(self.template, {
            'default_menu_item': rendered_default_item,
            'show_menu': bool(self.menu_items),
            'rendered_menu_items': rendered_menu_items,
        }, request=self.request)

    @cached_property
    def media(self):
        media = Media()
        for item in self.menu_items:
            media += item.media
        return media
