from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def cell_classname(context, row_index, col_index, table_header=None):
    classnames = context.get('classnames')
    if classnames:
        if table_header is not None:
            row_index += 1
        index = (row_index, col_index)
        cell_class = classnames.get(index)
        if cell_class:
            return mark_safe('class="{}"'.format(cell_class))
    return ''
