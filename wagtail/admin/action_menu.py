"""Handles rendering of the list of actions in the footer of the page create/edit views."""

from django.forms import Media, MediaDefiningClass
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtail.core import hooks
from wagtail.core.models import UserPagePermissionsProxy


class ActionMenuItem(metaclass=MediaDefiningClass):
    """Defines an item in the actions drop-up on the page creation/edit view"""
    order = 100  # default order index if one is not specified on init
    template = 'wagtailadmin/pages/action_menu/menu_item.html'

    label = ''
    name = None

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def is_shown(self, request, context):
        """
        Whether this action should be shown on this request; permission checks etc should go here.
        By default, actions are shown for unlocked pages, hidden for locked pages

        request = the current request object

        context = dictionary containing at least:
            'view' = 'create', 'edit' or 'revisions_revert'
            'page' (if view = 'edit' or 'revisions_revert') = the page being edited
            'parent_page' (if view = 'create') = the parent page of the page being created
            'user_page_permissions' = a UserPagePermissionsProxy for the current user, to test permissions against
        """
        return (context['view'] == 'create' or not context['page'].locked)

    def get_context(self, request, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()
        context.update({
            'label': self.label,
            'url': self.get_url(request, context),
            'name': self.name,
        })
        return context

    def get_url(self, request, context):
        return None

    def render_html(self, request, parent_context):
        context = self.get_context(request, parent_context)
        return render_to_string(self.template, context, request=request)


class PublishMenuItem(ActionMenuItem):
    name = 'action-publish'
    template = 'wagtailadmin/pages/action_menu/publish.html'

    def is_shown(self, request, context):
        if context['view'] == 'create':
            return context['user_page_permissions'].for_page(context['parent_page']).can_publish_subpage()
        else:  # view == 'edit' or 'revisions_revert'
            return (
                not context['page'].locked
                and context['user_page_permissions'].for_page(context['page']).can_publish()
            )

    def get_context(self, request, parent_context):
        context = super().get_context(request, parent_context)
        context['is_revision'] = (context['view'] == 'revisions_revert')
        return context


class SubmitForModerationMenuItem(ActionMenuItem):
    label = _("Submit for moderation")
    name = 'action-submit'

    def is_shown(self, request, context):
        if context['view'] == 'create':
            return True
        elif context['view'] == 'edit':
            return not context['page'].locked
        else:  # context == revisions_revert
            return False


class UnpublishMenuItem(ActionMenuItem):
    label = _("Unpublish")
    name = 'action-unpublish'

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and not context['page'].locked
            and context['user_page_permissions'].for_page(context['page']).can_unpublish()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:unpublish', args=(context['page'].id,))


class DeleteMenuItem(ActionMenuItem):
    name = 'action-delete'
    label = _("Delete")

    def is_shown(self, request, context):
        return (
            context['view'] == 'edit'
            and not context['page'].locked
            and context['user_page_permissions'].for_page(context['page']).can_delete()
        )

    def get_url(self, request, context):
        return reverse('wagtailadmin_pages:delete', args=(context['page'].id,))


BASE_PAGE_ACTION_MENU_ITEMS = None


def _get_base_page_action_menu_items():
    """
    Retrieve the global list of menu items for the page action menu,
    which may then be customised on a per-request basis
    """
    global BASE_PAGE_ACTION_MENU_ITEMS

    if BASE_PAGE_ACTION_MENU_ITEMS is None:
        BASE_PAGE_ACTION_MENU_ITEMS = [
            UnpublishMenuItem(order=10),
            DeleteMenuItem(order=20),
            PublishMenuItem(order=30),
            SubmitForModerationMenuItem(order=40),
        ]
        for hook in hooks.get_hooks('register_page_action_menu_item'):
            BASE_PAGE_ACTION_MENU_ITEMS.append(hook())

    return BASE_PAGE_ACTION_MENU_ITEMS


class PageActionMenu:
    template = 'wagtailadmin/pages/action_menu/menu.html'

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        self.context['user_page_permissions'] = UserPagePermissionsProxy(self.request.user)

        self.menu_items = [
            menu_item
            for menu_item in _get_base_page_action_menu_items()
            if menu_item.is_shown(self.request, self.context)
        ]

        self.menu_items.sort(key=lambda item: item.order)

        for hook in hooks.get_hooks('construct_page_action_menu'):
            hook(self.menu_items, self.request, self.context)

    def render_html(self):
        return render_to_string(self.template, {
            'show_menu': bool(self.menu_items),
            'rendered_menu_items': [
                menu_item.render_html(self.request, self.context)
                for menu_item in self.menu_items
            ]
        }, request=self.request)

    @cached_property
    def media(self):
        media = Media()
        for item in self.menu_items:
            media += item.media
        return media
