import re
from django import template
from django.utils.functional import cached_property

from wagtail.wagtailimages.models import Filter, SourceImageIOError

register = template.Library()


@register.tag(name="image")
def image(parser, token):

    bits = token.split_contents()[1:]
    image_expr = parser.compile_filter(bits[0])
    filter_spec = bits[1]   # Grab the filter Spec
    bits = bits[2:]     # Grab everything else

    as_bits = []
    compress = None

    # Parse out 'as' item and compression spec
    for index, item in enumerate(bits):
        if item == 'as' and bits[index + 1]:    # Check fo 'as' and alias
            bits = bits[:index]   # Reassign remaining bits
            as_bits = bits[index:]

        compression = re.match(r"^compress\-([0-9]{1,2})$", item)
        if compression:
            compress = compression.group(1)
            bits.pop(index)

    as_bit = False
    if len(as_bits) == 2 and as_bits[0] == 'as':
        as_bit = as_bits[1]

    # token is of the form {% image self.photo max-320x200 compress-55 %} - all additional tokens
    # should be kwargs, which become attributes
    attrs = {}
    for bit in bits:
        try:
            name, value = bit.split('=')
        except ValueError:
            raise template.TemplateSyntaxError("'image' tag should be of the form {% image self.photo max-320x200 [ compress-[compress-ratio] custom-attr=\"value\" ... ] %} or {% image self.photo max-320x200 as img %}")
        attrs[name] = parser.compile_filter(value)  # setup to resolve context variables as value

    return ImageNode(image_expr, filter_spec, attrs=attrs, output_var_name=as_bit, compress=compress)


class ImageNode(template.Node):
    def __init__(self, image_expr, filter_spec, output_var_name=None, attrs={}, compress=None):
        self.image_expr = image_expr
        self.output_var_name = output_var_name
        self.attrs = attrs
        self.filter_spec = filter_spec

        if compress:
            self.filter_spec = "%s_c_%s" % (self.filter_spec, compress)

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

        try:
            rendition = image.get_rendition(self.filter)
        except SourceImageIOError:
            # It's fairly routine for people to pull down remote databases to their
            # local dev versions without retrieving the corresponding image files.
            # In such a case, we would get a SourceImageIOError at the point where we try to
            # create the resized version of a non-existent image. Since this is a
            # bit catastrophic for a missing image, we'll substitute a dummy
            # Rendition object so that we just output a broken link instead.
            Rendition = image.renditions.model  # pick up any custom Image / Rendition classes that may be in use
            rendition = Rendition(image=image, width=0, height=0)
            rendition.file.name = 'not-found'

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
