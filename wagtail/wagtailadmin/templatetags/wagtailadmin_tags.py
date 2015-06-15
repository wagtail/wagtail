from __future__ import unicode_literals

from django.conf import settings
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import get_navigation_menu_items, UserPagePermissionsProxy, PageViewRestriction
from wagtail.wagtailcore.utils import camelcase_to_underscore, escape_script
from wagtail.wagtailadmin.menu import admin_menu


register = template.Library()

register.filter('intcomma', intcomma)

@register.inclusion_tag('wagtailadmin/shared/explorer_nav.html')
def explorer_nav():
    return {
        'nodes': get_navigation_menu_items()
    }


@register.inclusion_tag('wagtailadmin/shared/explorer_nav_child.html')
def explorer_subnav(nodes):
    return {
        'nodes': nodes
    }


@register.inclusion_tag('wagtailadmin/shared/main_nav.html', takes_context=True)
def main_nav(context):
    request = context['request']

    return {
        'menu_html': admin_menu.render_html(request),
        'request': request,
    }

@register.simple_tag
def main_nav_js():
    return admin_menu.media['js']


@register.filter("ellipsistrim")
def ellipsistrim(value, max_length):
    if len(value) > max_length:
        truncd_val = value[:max_length]
        if not len(value) == (max_length + 1) and value[max_length + 1] != " ":
            truncd_val = truncd_val[:truncd_val.rfind(" ")]
        return truncd_val + "..."
    return value


@register.filter
def fieldtype(bound_field):
    try:
        return camelcase_to_underscore(bound_field.field.__class__.__name__)
    except AttributeError:
        try:
            return camelcase_to_underscore(bound_field.__class__.__name__)
        except AttributeError:
            return ""


@register.filter
def widgettype(bound_field):
    try:
        return camelcase_to_underscore(bound_field.field.widget.__class__.__name__)
    except AttributeError:
        try:
            return camelcase_to_underscore(bound_field.widget.__class__.__name__)
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


@register.assignment_tag(takes_context=True)
def test_page_is_public(context, page):
    """
    Usage: {% test_page_is_public page as is_public %}
    Sets 'is_public' to True iff there are no page view restrictions in place on
    this page.
    Caches the list of page view restrictions in the context, to avoid repeated
    DB queries on repeated calls.
    """
    if 'all_page_view_restriction_paths' not in context:
        context['all_page_view_restriction_paths'] = PageViewRestriction.objects.select_related('page').values_list('page__path', flat=True)

    is_private = any([
        page.path.startswith(restricted_path)
        for restricted_path in context['all_page_view_restriction_paths']
    ])

    return not is_private


@register.simple_tag
def hook_output(hook_name):
    """
    Example: {% hook_output 'insert_editor_css' %}
    Whenever we have a hook whose functions take no parameters and return a string, this tag can be used
    to output the concatenation of all of those return values onto the page.
    Note that the output is not escaped - it is the hook function's responsibility to escape unsafe content.
    """
    snippets = [fn() for fn in hooks.get_hooks(hook_name)]
    return ''.join(snippets)


@register.assignment_tag
def usage_count_enabled():
    return getattr(settings, 'WAGTAIL_USAGE_COUNT_ENABLED', False)


@register.assignment_tag
def base_url_setting():
    return getattr(settings, 'BASE_URL', None)


class EscapeScriptNode(template.Node):
    TAG_NAME = 'escapescript'

    def __init__(self, nodelist):
        super(EscapeScriptNode, self).__init__()
        self.nodelist = nodelist

    def render(self, context):
        out = self.nodelist.render(context)
        return escape_script(out)

    @classmethod
    def handle(cls, parser, token):
        nodelist = parser.parse(('end' + EscapeScriptNode.TAG_NAME,))
        parser.delete_first_token()
        return cls(nodelist)

register.tag(EscapeScriptNode.TAG_NAME, EscapeScriptNode.handle)


# Helpers for Widget.render_with_errors, our extension to the Django widget API that allows widgets to
# take on the responsibility of rendering their own error messages
@register.filter
def render_with_errors(bound_field):
    """
    Usage: {{ field|render_with_errors }} as opposed to {{ field }}.
    If the field (a BoundField instance) has errors on it, and the associated widget implements
    a render_with_errors method, call that; otherwise, call the regular widget rendering mechanism.
    """
    widget = bound_field.field.widget
    if bound_field.errors and hasattr(widget, 'render_with_errors'):
        return widget.render_with_errors(bound_field.html_name, bound_field.value(), attrs={'id': bound_field.auto_id}, errors=bound_field.errors)
    else:
        return bound_field.as_widget()

@register.filter
def has_unrendered_errors(bound_field):
    """
    Return true if this field has errors that were not accounted for by render_with_errors, because
    the widget does not support the render_with_errors method
    """
    return bound_field.errors and not hasattr(bound_field.field.widget, 'render_with_errors')
