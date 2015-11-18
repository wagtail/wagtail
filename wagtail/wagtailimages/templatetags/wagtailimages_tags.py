from django import template
from django.utils.functional import cached_property

from wagtail.wagtailimages.models import Filter
from wagtail.wagtailimages.shortcuts import get_rendition_or_not_found

register = template.Library()


@register.tag(name="image")
def image(parser, token):
    bits = token.split_contents()[1:]
    image_expr = parser.compile_filter(bits[0])
    filter_spec = bits[1]
    bits = bits[2:]

    if len(bits) == 2 and bits[0] == 'as':
        # token is of the form {% image self.photo max-320x200 as img %}
        return ImageNode(image_expr, filter_spec, output_var_name=bits[1])
    else:
        # token is of the form {% image self.photo max-320x200 %} - all additional tokens
        # should be kwargs, which become attributes
        attrs = {}
        for bit in bits:
            try:
                name, value = bit.split('=')
            except ValueError:
                raise template.TemplateSyntaxError("'image' tag should be of the form {% image self.photo max-320x200 [ custom-attr=\"value\" ... ] %} or {% image self.photo max-320x200 as img %}")
            attrs[name] = parser.compile_filter(value)  # setup to resolve context variables as value

        return ImageNode(image_expr, filter_spec, attrs=attrs)


class ImageNode(template.Node):
    def __init__(self, image_expr, filter_spec, output_var_name=None, attrs={}):
        self.image_expr = image_expr
        self.output_var_name = output_var_name
        self.attrs = attrs
        self.filter_spec = filter_spec

    @cached_property
    def filter(self):
        _filter, _ = Filter.objects.get_or_create(spec=self.filter_spec)
        return _filter

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        rendition = get_rendition_or_not_found(image, self.filter)

        if self.output_var_name:
            # return the rendition object in the given variable
            context[self.output_var_name] = rendition
            return ''
        else:
            # render the rendition's image tag now
            resolved_attrs = {}
            for key in self.attrs:
                resolved_attrs[key] = self.attrs[key].resolve(context)
            return rendition.img_tag(resolved_attrs)
