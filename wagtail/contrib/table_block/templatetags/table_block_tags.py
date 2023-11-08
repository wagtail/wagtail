from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def cell_classname(context, row_index, col_index, table_header=None):
    classnames = context.get("classnames")
    if classnames:
        if table_header is not None:
            row_index += 1
        index = (row_index, col_index)
        cell_class = classnames.get(index)
        if cell_class:
            return mark_safe(f'class="{cell_class}"')
    return ""


@register.simple_tag(takes_context=True)
def cell_hidden(context, row_index, col_index, table_header=None):
    hidden = context.get("hidden")
    if hidden:
        if table_header is not None:
            row_index += 1
        index = (row_index, col_index)
        return hidden.get(index, False)
    return False


@register.simple_tag(takes_context=True)
def cell_span(context, row_index, col_index, table_header=None):
    spans = context.get("spans")
    if spans:
        if table_header is not None:
            row_index += 1
        index = (row_index, col_index)
        cell_span = spans.get(index)
        if cell_span:
            return mark_safe(
                'rowspan="{}" colspan="{}"'.format(
                    cell_span["rowspan"],
                    cell_span["colspan"],
                )
            )
    return ""
