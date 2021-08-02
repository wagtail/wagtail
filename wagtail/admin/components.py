from django.forms import MediaDefiningClass
from django.template.loader import render_to_string


class Component(metaclass=MediaDefiningClass):
    """
    Implements the common pattern of an object that knows how to render itself to an HTML page.

    Subclasses should provide a 'template' attribute, or override render_html.
    """
    def get_context(self, request, parent_context):
        return parent_context.copy()

    def render_html(self, request, parent_context):
        context = self.get_context(request, parent_context)
        return render_to_string(self.template, context, request=request)
