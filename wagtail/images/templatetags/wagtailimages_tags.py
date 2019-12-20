import re

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch
from django.utils.functional import cached_property

from wagtail.images.models import Filter
from wagtail.images.shortcuts import get_rendition_or_not_found
from wagtail.images.views.serve import generate_image_url


register = template.Library()
allowed_filter_pattern = re.compile(r"^[A-Za-z0-9_\-\.]+$")


@register.tag(name="image")
def image(parser, token):
    bits = token.split_contents()[1:]
    image_expr = parser.compile_filter(bits[0])
    bits = bits[1:]

    filter_specs = []
    attrs = {}
    output_var_name = None

    as_context = False  # if True, the next bit to be read is the output variable name
    is_valid = True

    for bit in bits:
        if bit == 'as':
            # token is of the form {% image self.photo max-320x200 as img %}
            as_context = True
        elif as_context:
            if output_var_name is None:
                output_var_name = bit
            else:
                # more than one item exists after 'as' - reject as invalid
                is_valid = False
        else:
            try:
                name, value = bit.split('=')
                attrs[name] = parser.compile_filter(value)  # setup to resolve context variables as value
            except ValueError:
                if allowed_filter_pattern.match(bit):
                    filter_specs.append(bit)
                else:
                    raise template.TemplateSyntaxError(
                        "filter specs in 'image' tag may only contain A-Z, a-z, 0-9, dots, hyphens and underscores. "
                        "(given filter: {})".format(bit)
                    )

    if as_context and output_var_name is None:
        # context was introduced but no variable given ...
        is_valid = False

    if output_var_name and attrs:
        # attributes are not valid when using the 'as img' form of the tag
        is_valid = False

    if len(filter_specs) == 0:
        # there must always be at least one filter spec provided
        is_valid = False

    if len(bits) == 0:
        # no resize rule provided eg. {% image page.image %}
        raise template.TemplateSyntaxError(
            "no resize rule provided. "
            "'image' tag should be of the form {% image self.photo max-320x200 [ custom-attr=\"value\" ... ] %} "
            "or {% image self.photo max-320x200 as img %}"
        )

    if is_valid:
        return ImageNode(image_expr, '|'.join(filter_specs), attrs=attrs, output_var_name=output_var_name)
    else:
        raise template.TemplateSyntaxError(
            "'image' tag should be of the form {% image self.photo max-320x200 [ custom-attr=\"value\" ... ] %} "
            "or {% image self.photo max-320x200 as img %}"
        )


class ImageNode(template.Node):
    def __init__(self, image_expr, filter_spec, output_var_name=None, attrs={}):
        self.image_expr = image_expr
        self.output_var_name = output_var_name
        self.attrs = attrs
        self.filter_spec = filter_spec

    @cached_property
    def filter(self):
        return Filter(spec=self.filter_spec)

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        if not hasattr(image, 'get_rendition'):
            raise ValueError("image tag expected an Image object, got %r" % image)

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


@register.simple_tag()
def image_url(image, filter_spec, viewname='wagtailimages_serve'):
    try:
        return generate_image_url(image, filter_spec, viewname)
    except NoReverseMatch:
        raise ImproperlyConfigured(
            "'image_url' tag requires the " + viewname + " view to be configured. Please see "
            "https://docs.wagtail.io/en/stable/advanced_topics/images/image_serve_view.html#setup for instructions."
        )
