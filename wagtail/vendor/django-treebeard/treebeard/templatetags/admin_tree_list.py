# -*- coding: utf-8 -*-

from django.template import Library
from treebeard.templatetags import needs_checkboxes


register = Library()
CHECKBOX_TMPL = ('<input type="checkbox" class="action-select" value="%d" '
                 'name="_selected_action" />')


def _line(context, node, request):
    if 't' in request.GET and request.GET['t'] == 'id':
        raw_id_fields = """
        onclick="opener.dismissRelatedLookupPopup(window, '%d'); return false;"
        """ % (node.pk,)
    else:
        raw_id_fields = ''
    output = ''
    if needs_checkboxes(context):
        output += CHECKBOX_TMPL % node.pk
    return output + '<a href="%d/" %s>%s</a>' % (
        node.pk, raw_id_fields, str(node))


def _subtree(context, node, request):
    tree = ''
    for subnode in node.get_children():
        tree += '<li>%s</li>' % _subtree(context, subnode, request)
    if tree:
        tree = '<ul>%s</ul>' % tree
    return _line(context, node, request) + tree


@register.simple_tag(takes_context=True)
def result_tree(context, cl, request):
    tree = ''
    for root_node in cl.model.get_root_nodes():
        tree += '<li>%s</li>' % _subtree(context, root_node, request)
    return "<ul>%s</ul>" % tree
