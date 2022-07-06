from django.template import Library, Node
from django.template.defaulttags import token_kwargs

from wagtail.contrib.settings.context_processors import SettingProxy
from wagtail.models import Site

register = Library()


class SettingsNode(Node):
    @staticmethod
    def get_settings_object(context, use_default_site=False):
        if use_default_site:
            return SettingProxy(request_or_site=Site.objects.get(is_default_site=True))
        elif "request" in context:
            return SettingProxy(request_or_site=context["request"])

        # Try with `request_or_site=None` in case we're dealing with a generic
        # setting.
        return SettingProxy(request_or_site=None)

    def __init__(self, kwargs, target_var):
        self.kwargs = kwargs
        self.target_var = target_var

    def render(self, context):
        resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}
        context[self.target_var] = self.get_settings_object(context, **resolved_kwargs)
        return ""


@register.tag
def get_settings(parser, token):
    bits = token.split_contents()[1:]
    target_var = "settings"
    if len(bits) >= 2 and bits[-2] == "as":
        target_var = bits[-1]
        bits = bits[:-2]
    kwargs = token_kwargs(bits, parser) if bits else {}
    return SettingsNode(kwargs, target_var)
