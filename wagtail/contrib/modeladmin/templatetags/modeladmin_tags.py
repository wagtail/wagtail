from __future__ import absolute_import, unicode_literals

import datetime

import django
from django.contrib.admin.templatetags.admin_list import ResultList, result_headers
from django.contrib.admin.utils import display_for_field, display_for_value, lookup_field
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template import Library
from django.template.loader import get_template
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

register = Library()


def items_for_result(view, result):
    """
    Generates the actual list of data.
    """
    modeladmin = view.model_admin
    for field_name in view.list_display:
        empty_value_display = modeladmin.get_empty_value_display(field_name)
        row_classes = ['field-%s' % field_name]
        try:
            f, attr, value = lookup_field(field_name, result, modeladmin)
        except ObjectDoesNotExist:
            result_repr = empty_value_display
        else:
            empty_value_display = getattr(
                attr, 'empty_value_display', empty_value_display)
            if f is None or f.auto_created:
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if boolean or not value:
                    allow_tags = True
                if django.VERSION >= (1, 9):
                    result_repr = display_for_value(
                        value, empty_value_display, boolean)
                else:
                    result_repr = display_for_value(value, boolean)

                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if allow_tags:
                    result_repr = mark_safe(result_repr)
                if isinstance(value, (datetime.date, datetime.time)):
                    row_classes.append('nowrap')
            else:
                if isinstance(f, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = empty_value_display
                    else:
                        result_repr = field_val
                else:
                    if django.VERSION >= (1, 9):
                        result_repr = display_for_field(
                            value, f, empty_value_display)
                    else:
                        result_repr = display_for_field(value, f)

                if isinstance(f, (
                    models.DateField, models.TimeField, models.ForeignKey)
                ):
                    row_classes.append('nowrap')
        if force_text(result_repr) == '':
            result_repr = mark_safe('&nbsp;')
        row_classes.extend(
            modeladmin.get_extra_class_names_for_field_col(field_name, result))
        row_attrs_dict = modeladmin.get_extra_attrs_for_field_col(
            field_name, result)
        row_attrs_dict['class'] = ' ' . join(row_classes)
        row_attrs = ''.join(
            ' %s="%s"' % (key, val) for key, val in row_attrs_dict.items())
        row_attrs_safe = mark_safe(row_attrs)
        yield format_html('<td{}>{}</td>', row_attrs_safe, result_repr)


def results(view, object_list):
    for item in object_list:
        yield ResultList(None, items_for_result(view, item))


@register.inclusion_tag("modeladmin/includes/result_list.html",
                        takes_context=True)
def result_list(context):
    """
    Displays the headers and data list together
    """
    view = context['view']
    object_list = context['object_list']
    headers = list(result_headers(view))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    context.update({
        'result_headers': headers,
        'num_sorted_fields': num_sorted_fields,
        'results': list(results(view, object_list))})
    return context


@register.simple_tag
def pagination_link_previous(current_page, view):
    if current_page.has_previous():
        previous_page_number0 = current_page.previous_page_number() - 1
        return format_html(
            '<li class="prev"><a href="%s" class="icon icon-arrow-left">%s'
            '</a></li>' %
            (view.get_query_string({view.PAGE_VAR: previous_page_number0}),
                _('Previous'))
        )
    return ''


@register.simple_tag
def pagination_link_next(current_page, view):
    if current_page.has_next():
        next_page_number0 = current_page.next_page_number() - 1
        return format_html(
            '<li class="next"><a href="%s" class="icon icon-arrow-right-after"'
            '>%s</a></li>' %
            (view.get_query_string({view.PAGE_VAR: next_page_number0}),
                _('Next'))
        )
    return ''


@register.inclusion_tag(
    "modeladmin/includes/search_form.html", takes_context=True)
def search_form(context):
    context.update({'search_var': context['view'].SEARCH_VAR})
    return context


@register.simple_tag
def admin_list_filter(view, spec):
    template_name = spec.template
    if template_name == 'admin/filter.html':
        template_name = 'modeladmin/includes/filter.html'
    tpl = get_template(template_name)
    return tpl.render({
        'title': spec.title,
        'choices': list(spec.choices(view)),
        'spec': spec,
    })


@register.inclusion_tag(
    "modeladmin/includes/result_row.html", takes_context=True)
def result_row_display(context, index):
    obj = context['object_list'][index]
    view = context['view']
    context.update({
        'obj': obj,
        'action_buttons': view.get_buttons_for_obj(obj),
    })
    return context


@register.inclusion_tag(
    "modeladmin/includes/result_row_value.html", takes_context=True)
def result_row_value_display(context, index):
    add_action_buttons = False
    item = context['item']
    closing_tag = mark_safe(item[-5:])
    request = context['request']
    model_admin = context['view'].model_admin
    field_name = model_admin.get_list_display(request)[index]
    if field_name == model_admin.get_list_display_add_buttons(request):
        add_action_buttons = True
        item = mark_safe(item[0:-5])
    context.update({
        'item': item,
        'add_action_buttons': add_action_buttons,
        'closing_tag': closing_tag,
    })
    return context


@register.filter
def get_content_type_for_obj(obj):
    return obj.__class__._meta.verbose_name
