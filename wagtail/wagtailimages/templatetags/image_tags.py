from django import template

from wagtail.wagtailimages.models import Filter

register = template.Library()

# Local cache of filters, avoid hitting the DB
filters = {}


@register.tag(name="image")
def image(parser, token):
    bits = token.split_contents()[1:]
    image_var = bits[0]
    filter_spec = bits[1]
    bits = bits[2:]

    if len(bits) == 2 and bits[0] == 'as':
        # token is of the form {% image self.photo max-320x200 as img %}
        return ImageNode(image_var, filter_spec, output_var_name=bits[1])
    else:
        # token is of the form {% image self.photo max-320x200 %} - all additional tokens
        # should be kwargs, which become attributes
        attrs = {}
        for bit in bits:
            try:
                name, value = bit.split('=')
            except ValueError:
                raise template.TemplateSyntaxError("'image' tag should be of the form {% image self.photo max-320x200 [ custom-attr=\"value\" ... ] %} or {% image self.photo max-320x200 as img %}")
            attrs[name] = parser.compile_filter(value) # setup to resolve context variables as value

        return ImageNode(image_var, filter_spec, attrs=attrs)


class ImageNode(template.Node):
    def __init__(self, image_var_name, filter_spec, output_var_name=None, attrs={}):
        self.image_var = template.Variable(image_var_name)
        self.output_var_name = output_var_name
        self.attrs = attrs

        if filter_spec not in filters:
            filters[filter_spec], _ = Filter.objects.get_or_create(spec=filter_spec)
        self.filter = filters[filter_spec]

    def render(self, context):
        try:
            image = self.image_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not image:
            return ''

        try:
            rendition = image.get_rendition(self.filter)
        except IOError:
            # It's fairly routine for people to pull down remote databases to their
            # local dev versions without retrieving the corresponding image files.
            # In such a case, we would get an IOError at the point where we try to
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
