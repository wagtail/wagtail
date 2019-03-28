import re

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template import Node, TemplateSyntaxError, VariableDoesNotExist
from django.urls import NoReverseMatch
from wagtail.images.models import Filter
from wagtail.images.shortcuts import get_rendition_or_not_found
from wagtail.images.views.serve import generate_image_url

register = template.Library()

# inspired by django.template.base.kwarg_re but this one here doesn't allow the name to
# be optional.
# we need to support quotes because we also want to support attribute names to be
# variables.
kwarg_re = re.compile(r"(?P<attr_name>['\".]?[\w._-]+['\"]?)=(?P<attr_value>.+)")


class ImageNode(Node):
    def __init__(self, image_expr, filter_expr, additional_tag_attrs, asvar):
        self.image_expr = image_expr
        self.filter_expr = filter_expr
        self.additional_tag_attrs = additional_tag_attrs
        self.asvar = asvar

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
        except VariableDoesNotExist:
            return ""

        if not image:
            return ""

        filter_spec = self.filter_expr.resolve(context).replace(" ", "|")
        rendition = get_rendition_or_not_found(image, Filter(filter_spec))

        if self.asvar:
            # return the rendition object in the given variable
            context[self.asvar] = rendition
            return ""
        else:
            # render the renditions image tag now
            resolved_attrs = {}
            for attr_data in self.additional_tag_attrs.values():
                name_expr = attr_data["name"]
                name = name_expr.resolve(context)
                value_expr = attr_data["value"]
                value = value_expr.resolve(context)
                resolved_attrs[name] = value
            return rendition.img_tag(resolved_attrs)


@register.tag
def image(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(
            "'{}' takes at least two arguments, an image and the filter-spec.".format(
                bits[0]
            )
        )

    image_expr = parser.compile_filter(bits[1])
    filter_spec_expr = parser.compile_filter(bits[2])
    bits = bits[3:]
    asvar = None
    if len(bits) >= 2 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]

    # Support for additional image tag attributes
    kwargs = {}
    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError(
                'Invalid kwarg in image tag "{}". '
                "Everything after the filter spec must either be a kwarg or "
                "specify the context variable to store into.".format(bit)
            )
        name, value = match.groups()
        if name in kwargs:
            raise TemplateSyntaxError(
                "'{}' seen multiple times in your image tag.".format(name)
            )
        kwargs[name] = {
            # TODO: We support having variables storing the names. But does it make
            # sense to support that?
            "name": parser.compile_filter(name),
            "value": parser.compile_filter(value),
        }

    return ImageNode(image_expr, filter_spec_expr, kwargs, asvar)


class ImageUrlNode(Node):
    def __init__(self, image_expr, filter_expr, viewname_expr, asvar):
        self.image_expr = image_expr
        self.filter_expr = filter_expr
        self.viewname_expr = viewname_expr
        self.asvar = asvar

    def render(self, context):
        try:
            image = self.image_expr.resolve(context)
        except VariableDoesNotExist:
            return ""

        if not image:
            return ""

        filter_spec = self.filter_expr.resolve(context).replace(" ", "|")
        viewname = "wagtailimages_serve"
        if self.viewname_expr:
            viewname = self.viewname_expr.resolve(context)

        try:
            rendition_url = generate_image_url(image, filter_spec, viewname)
        except NoReverseMatch:
            raise ImproperlyConfigured(
                "'image_url' tag requires the "
                + viewname
                + " view to be configured. Please see "
                "https://docs.wagtail.io/en/stable/advanced_topics/images/image_serve_view.html#setup for instructions."
            )

        if self.asvar:
            # return the rendition object in the given variable
            context[self.asvar] = rendition_url
            return ""
        else:
            return rendition_url


@register.tag
def image_url(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(
            "'{}' takes at least two arguments, an image and the filter-spec.".format(
                bits[0]
            )
        )

    image_expr = parser.compile_filter(bits[1])
    filter_spec_expr = parser.compile_filter(bits[2])
    bits = bits[3:]
    asvar = None
    if len(bits) >= 2 and bits[-2] == "as":
        asvar = bits[-1]
        bits = bits[:-2]
    viewname_expr = None
    if len(bits) == 1:
        viewname_expr = parser.compile_filter(bits[0])

    return ImageUrlNode(image_expr, filter_spec_expr, viewname_expr, asvar)
