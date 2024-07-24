from django.template import Library
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin.options import TO_FIELD_VAR

from treebeard.templatetags import needs_checkboxes


register = Library()
CHECKBOX_TMPL = ('<input type="checkbox" class="action-select" value="{}" '
                 'name="_selected_action" />')


def _line(context, node, request):
    pk_field = node._meta.model._meta.pk.attname
    if TO_FIELD_VAR in request.GET and request.GET[TO_FIELD_VAR] == pk_field:
        raw_id_fields = format_html("""
        onclick="opener.dismissRelatedLookupPopup(window, '{}'); return false;"
        """, node.pk)
    else:
        raw_id_fields = ''
    output = ''
    if needs_checkboxes(context):
        output += format_html(CHECKBOX_TMPL, node.pk)
    return output + format_html(
        '<a href="{}/" {}>{}</a>',
        node.pk, mark_safe(raw_id_fields), str(node))


def _subtree(context, node, request):
    tree = ''
    for subnode in node.get_children():
        tree += format_html(
            '<li>{}</li>',
            mark_safe(_subtree(context, subnode, request)))
    if tree:
        tree = format_html('<ul>{}</ul>', mark_safe(tree))
    return _line(context, node, request) + tree


@register.simple_tag(takes_context=True)
def result_tree(context, cl, request):
    tree = ''
    for root_node in cl.model.get_root_nodes():
        tree += format_html(
            '<li>{}</li>', mark_safe(_subtree(context, root_node, request)))
    return format_html("<ul>{}</ul>", mark_safe(tree))
