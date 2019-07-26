from django.template import Library

from wagtail.core.models import get_site_model

from ..context_processors import SettingsProxy

register = Library()


@register.simple_tag(takes_context=True)
def get_settings(context, use_default_site=False):
    if use_default_site:
        Site = get_site_model()
        site = Site.objects.get(is_default_site=True)
    elif 'request' in context:
        site = context['request'].site
    else:
        raise RuntimeError('No request found in context, and use_default_site '
                           'flag not set')

    context['settings'] = SettingsProxy(site)
    return ''
