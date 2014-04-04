from django import template
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailcore.models import get_navigation_menu_items
from wagtail.wagtailcore.util import camelcase_to_underscore

from wagtail.wagtailsnippets.permissions import user_can_edit_snippets  # TODO: reorganise into pluggable architecture so that wagtailsnippets registers its own menu item

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


@register.assignment_tag
def get_wagtailadmin_tab_urls():
    resolver = urlresolvers.get_resolver(None)
    return [
        (key, value[2].get("title", key))
        for key, value
        in resolver.reverse_dict.items()
        if isinstance(key, basestring) and key.startswith('wagtailadmin_tab_')
    ]


@register.inclusion_tag('wagtailadmin/shared/main_nav.html', takes_context=True)
def main_nav(context):
    menu_items = [
        MenuItem(_('Explorer'), '#', classnames='icon icon-folder-open-inverse dl-trigger', order=100),
        MenuItem(_('Search'), urlresolvers.reverse('wagtailadmin_pages_search'), classnames='icon icon-search', order=200),
    ]

    request = context['request']
    user = request.user

    if user.has_perm('wagtailimages.add_image'):
        menu_items.append(
            MenuItem(_('Images'), urlresolvers.reverse('wagtailimages_index'), classnames='icon icon-image', order=300)
        )
    if user.has_perm('wagtaildocs.add_document'):
        menu_items.append(
            MenuItem(_('Documents'), urlresolvers.reverse('wagtaildocs_index'), classnames='icon icon-doc-full-inverse', order=400)
        )

    if user_can_edit_snippets(user):
        menu_items.append(
            MenuItem(_('Snippets'), urlresolvers.reverse('wagtailsnippets_index'), classnames='icon icon-snippet', order=500)
        )

    if user.has_module_perms('auth'):
        menu_items.append(
            MenuItem(_('Users'), urlresolvers.reverse('wagtailusers_index'), classnames='icon icon-user', order=600)
        )

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
