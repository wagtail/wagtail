from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch

from wagtail.images.models import Filter, ResponsiveImage
from wagtail.images.shortcuts import (
    get_rendition_or_not_found,
    get_renditions_or_not_found,
)
from wagtail.images.utils import to_svg_safe_spec
from wagtail.images.views.serve import generate_image_url

register = template.Library()


def image(parser, token):
    """
    Image tag parser implementation. Shared between all image tags supporting filter specs
    as space-separated arguments.
    """
    tag_name, *bits = token.split_contents()
    image_expr = parser.compile_filter(bits[0])
    bits = bits[1:]

    filter_specs = []
    attrs = {}
    output_var_name = None

    as_context = False  # if True, the next bit to be read is the output variable name
    error_messages = []

    multi_rendition = tag_name != "image"
    preserve_svg = False

    for bit in bits:
        if bit == "as":
            # token is of the form {% image self.photo max-320x200 as img %}
            as_context = True
        elif as_context:
            if output_var_name is None:
                output_var_name = bit
            else:
                # more than one item exists after 'as' - reject as invalid
                error_messages.append("More than one variable name after 'as'")
        elif bit == "preserve-svg":
            preserve_svg = True
        else:
            try:
                name, value = bit.split("=")
                attrs[name] = parser.compile_filter(
                    value
                )  # setup to resolve context variables as value
            except ValueError:
                allowed_pattern = (
                    Filter.expanding_spec_pattern
                    if multi_rendition
                    else Filter.spec_pattern
                )
                if allowed_pattern.match(bit):
                    filter_specs.append(bit)
                else:
                    raise template.TemplateSyntaxError(
                        "filter specs in image tags may only contain A-Z, a-z, 0-9, dots, hyphens and underscores (and commas and curly braces for multi-image tags). "
                        "(given filter: {})".format(bit)
                    )

    if as_context and output_var_name is None:
        # context was introduced but no variable given ...
        error_messages.append("Missing a variable name after 'as'")

    if output_var_name and attrs:
        # attributes are not valid when using the 'as img' form of the tag
        error_messages.append("Do not use attributes with 'as' context assignments")

    if len(filter_specs) == 0:
        # there must always be at least one filter spec provided
        error_messages.append("Image tags must be used with at least one filter spec")

    if len(bits) == 0:
        # no resize rule provided eg. {% image page.image %}
        error_messages.append("No resize rule provided")

    if len(error_messages) == 0:
        Node = {
            "image": ImageNode,
            "srcset_image": SrcsetImageNode,
        }
        return Node[tag_name](
            image_expr,
            filter_specs,
            attrs=attrs,
            output_var_name=output_var_name,
            preserve_svg=preserve_svg,
        )
    else:
        errors = "; ".join(error_messages)
        raise template.TemplateSyntaxError(
            f"Invalid arguments provided to {tag_name}: {errors}. "
            'Image tags should be of the form {% image self.photo max-320x200 [ custom-attr="value" ... ] %} '
            "or {% image self.photo max-320x200 as img %}. "
        )


register.tag("image", image)
register.tag("srcset_image", image)


class ImageNode(template.Node):
    def __init__(
        self,
        image_expr,
        filter_specs,
        output_var_name=None,
        attrs={},
        preserve_svg=False,
    ):
        self.image_expr = image_expr
        self.output_var_name = output_var_name
        self.attrs = attrs
        self.filter_specs = filter_specs
        self.preserve_svg = preserve_svg

    def get_filter(self, preserve_svg=False):
        if preserve_svg:
            return Filter(to_svg_safe_spec(self.filter_specs))
        return Filter(spec="|".join(self.filter_specs))

    def validate_image(self, context):
        try:
            image = self.image_expr.resolve(context)
        except template.VariableDoesNotExist:
            return

        if not image:
            if self.output_var_name:
                context[self.output_var_name] = None
            return

        if not hasattr(image, "get_rendition"):
            raise ValueError(
                "Image template tags expect an Image object, got %r" % image
            )

        return image

    def render(self, context):
        image = self.validate_image(context)

        if not image:
            return ""

        rendition = get_rendition_or_not_found(
            image,
            self.get_filter(preserve_svg=self.preserve_svg and image.is_svg()),
        )

        if self.output_var_name:
            # return the rendition object in the given variable
            context[self.output_var_name] = rendition
            return ""
        else:
            # render the rendition's image tag now
            resolved_attrs = {}
            for key in self.attrs:
                resolved_attrs[key] = self.attrs[key].resolve(context)
            return rendition.img_tag(resolved_attrs)


class SrcsetImageNode(ImageNode):
    def get_filters(self, preserve_svg=False):
        filter_specs = Filter.expand_spec(self.filter_specs)
        if preserve_svg:
            return [Filter(to_svg_safe_spec(f)) for f in filter_specs]
        return [Filter(spec=f) for f in filter_specs]

    def render(self, context):
        image = self.validate_image(context)

        if not image:
            return ""

        specs = self.get_filters(preserve_svg=self.preserve_svg and image.is_svg())
        renditions = get_renditions_or_not_found(image, specs)

        if self.output_var_name:
            # Wrap the renditions in ResponsiveImage object, to support both
            # rendering as-is and access to the data.
            context[self.output_var_name] = ResponsiveImage(renditions)
            return ""

        resolved_attrs = {}
        for key in self.attrs:
            resolved_attrs[key] = self.attrs[key].resolve(context)

        return ResponsiveImage(renditions, resolved_attrs).__html__()


@register.simple_tag()
def image_url(image, filter_spec, viewname="wagtailimages_serve"):
    try:
        return generate_image_url(image, filter_spec, viewname)
    except NoReverseMatch:
        raise ImproperlyConfigured(
            "'image_url' tag requires the "
            + viewname
            + " view to be configured. Please see "
            "https://docs.wagtail.org/en/stable/advanced_topics/images/image_serve_view.html#setup for instructions."
        )
