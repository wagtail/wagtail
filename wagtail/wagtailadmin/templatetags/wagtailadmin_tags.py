from django import template
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailcore.models import get_navigation_menu_items, UserPagePermissionsProxy
from wagtail.wagtailcore.util import camelcase_to_underscore


register = template.Library()


@register.inclusion_tag('wagtailadmin/shared/explorer_nav.html')
def explorer_nav():
    return {
        'nodes': get_navigation_menu_items()
    }


@register.inclusion_tag('wagtailadmin/shared/explorer_nav.html')
def explorer_subnav(nodes):
    return {
        'nodes': nodes
    }


@register.inclusion_tag('wagtailadmin/shared/main_nav.html', takes_context=True)
def main_nav(context):
    menu_items = [
        MenuItem(_('Explorer'), '#', classnames='icon icon-folder-open-inverse dl-trigger', order=100),
        MenuItem(_('Search'), urlresolvers.reverse('wagtailadmin_pages_search'), classnames='icon icon-search', order=200),
    ]

    request = context['request']

    for fn in hooks.get_hooks('construct_main_menu'):
        fn(request, menu_items)

    return {
        'menu_items': sorted(menu_items, key=lambda i: i.order),
        'request': request,
    }


@register.filter("ellipsistrim")
def ellipsistrim(value, max_length):
    if len(value) > max_length:
        truncd_val = value[:max_length]
        if not len(value) == max_length+1 and value[max_length+1] != " ":
            truncd_val = truncd_val[:truncd_val.rfind(" ")]
        return truncd_val + "..."
    return value


@register.filter
def fieldtype(bound_field):
    try:
        return camelcase_to_underscore(bound_field.field.__class__.__name__)
    except AttributeError:
        return ""


@register.filter
def meta_description(model):
    try:
        return model.model_class()._meta.description
    except:
        return ""


@register.assignment_tag(takes_context=True)
def page_permissions(context, page):
    """
    Usage: {% page_permissions page as page_perms %}
    Sets the variable 'page_perms' to a PagePermissionTester object that can be queried to find out
    what actions the current logged-in user can perform on the given page.
    """
    # Create a UserPagePermissionsProxy object to represent the user's global permissions, and
    # cache it in the context for the duration of the page request, if one does not exist already
    if 'user_page_permissions' not in context:
        context['user_page_permissions'] = UserPagePermissionsProxy(context['request'].user)

    # Now retrieve a PagePermissionTester from it, specific to the given page
    return context['user_page_permissions'].for_page(page)


@register.simple_tag
def hook_output(hook_name):
    """
    Example: {% hook_output 'insert_editor_css' %}
    Whenever we have a hook whose functions take no parameters and return a string, this tag can be used
    to output the concatenation of all of those return values onto the page.
    Note that the output is not escaped - it is the hook function's responsibility to escape unsafe content.
    """
    snippets = [fn() for fn in hooks.get_hooks(hook_name)]
    return u''.join(snippets)
