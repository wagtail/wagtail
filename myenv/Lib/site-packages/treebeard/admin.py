"""Django admin support for treebeard"""

import sys

from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseBadRequest
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_str

from treebeard.exceptions import (InvalidPosition, MissingNodeOrderBy,
                                  InvalidMoveToDescendant, PathOverflow)
from treebeard.al_tree import AL_Node


class TreeAdmin(admin.ModelAdmin):
    """Django Admin class for treebeard."""

    change_list_template = 'admin/tree_change_list.html'

    def get_queryset(self, request):
        if issubclass(self.model, AL_Node):
            # AL Trees return a list instead of a QuerySet for .get_tree()
            # So we're returning the regular .get_queryset cause we will use
            # the old admin
            return super().get_queryset(request)
        else:
            return self.model.get_tree()

    def changelist_view(self, request, extra_context=None):
        if issubclass(self.model, AL_Node):
            # For AL trees, use the old admin display
            self.change_list_template = 'admin/tree_list.html'
        if extra_context is None:
            extra_context = {}
        request_context = any(
            map(
                lambda tmpl:
                    tmpl.get('BACKEND', None) == 'django.template.backends.django.DjangoTemplates' and
                    tmpl.get('APP_DIRS', False) and
                    'django.template.context_processors.request' in tmpl.get('OPTIONS', {}).get('context_processors', []),
                settings.TEMPLATES
            )
        )
        lacks_request = ('request' not in extra_context and not request_context)
        if lacks_request:
            extra_context['request'] = request
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        """
        Adds a url to move nodes to this admin
        """
        urls = super().get_urls()
        from django.views.i18n import JavaScriptCatalog

        jsi18n_url = path('jsi18n/',
            JavaScriptCatalog.as_view(packages=['treebeard']),
            name='javascript-catalog'
        )

        new_urls = [
            path('move/', self.admin_site.admin_view(self.move_node), ),
            jsi18n_url,
        ]
        return new_urls + urls

    def get_node(self, node_id):
        return self.model.objects.get(pk=node_id)

    def try_to_move_node(self, as_child, node, pos, request, target):
        try:
            node.move(target, pos=pos)
            # Call the save method on the (reloaded) node in order to trigger
            # possible signal handlers etc.
            node = self.get_node(node.pk)
            node.save()
        except (MissingNodeOrderBy, PathOverflow, InvalidMoveToDescendant,
                InvalidPosition):
            e = sys.exc_info()[1]
            # An error was raised while trying to move the node, then set an
            # error message and return 400, this will cause a reload on the
            # client to show the message
            messages.error(request,
                           _('Exception raised while moving node: %s') % _(
                               force_str(e)))
            return HttpResponseBadRequest('Exception raised during move')
        if as_child:
            msg = _('Moved node "%(node)s" as child of "%(other)s"')
        else:
            msg = _('Moved node "%(node)s" as sibling of "%(other)s"')
        messages.info(request, msg % {'node': node, 'other': target})
        return HttpResponse('OK')

    def move_node(self, request):
        try:
            node_id = request.POST['node_id']
            target_id = request.POST['sibling_id']
            as_child = bool(int(request.POST.get('as_child', 0)))
        except (KeyError, ValueError):
            # Some parameters were missing return a BadRequest
            return HttpResponseBadRequest('Malformed POST params')

        node = self.get_node(node_id)
        target = self.get_node(target_id)
        is_sorted = True if node.node_order_by else False

        pos = {
            (True, True): 'sorted-child',
            (True, False): 'last-child',
            (False, True): 'sorted-sibling',
            (False, False): 'left',
        }[as_child, is_sorted]
        return self.try_to_move_node(as_child, node, pos, request, target)


def admin_factory(form_class):
    """Dynamically build a TreeAdmin subclass for the given form class.

    :param form_class:
    :return: A TreeAdmin subclass.
    """
    return type(
        form_class.__name__ + 'Admin',
        (TreeAdmin,),
        dict(form=form_class))
