from django.template import Library, Node
from django.template.defaulttags import token_kwargs

from wagtail.core.models import Site

from ..context_processors import SettingsProxy


register = Library()


class GetSettingsNode(Node):
    def __init__(self, kwargs, target_var):
        self.kwargs = kwargs
        self.target_var = target_var

    @staticmethod
    def get_settings_object(context, use_default_site=False):
        if use_default_site:
            site = Site.objects.get(is_default_site=True)
            return SettingsProxy(site)
        if 'request' in context:
            return SettingsProxy(context['request'])

        raise RuntimeError('No request found in context, and use_default_site flag not set')

    def render(self, context):
        resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        context[self.target_var] = self.get_settings_object(context, **resolved_kwargs)
        return ''


@register.tag
def get_settings(parser, token):
    bits = token.split_contents()[1:]
    target_var = 'settings'
    if len(bits) >= 2 and bits[-2] == 'as':
        target_var = bits[-1]
        bits = bits[:-2]
    kwargs = token_kwargs(bits, parser) if bits else {}
    return GetSettingsNode(kwargs, target_var)
