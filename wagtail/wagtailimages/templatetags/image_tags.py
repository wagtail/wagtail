from django import template

from wagtail.wagtailimages.models import Filter, Rendition

register = template.Library()


@register.tag(name="image")
def image(parser, token):
    args = token.split_contents()

    if len(args) == 3:
        # token is of the form {% image self.photo max-320x200 %}
        tag_name, image_var, filter_spec = args
        return ImageNode(image_var, filter_spec)

    elif len(args) == 5:
        # token is of the form {% image self.photo max-320x200 as img %}
        tag_name, image_var, filter_spec, as_token, out_var = args

        if as_token != 'as':
            raise template.TemplateSyntaxError("'image' tag should be of the form {%% image self.photo max-320x200 %%} or {%% image self.photo max-320x200 as img %%}")

        return ImageNode(image_var, filter_spec, out_var)

    else:
        raise template.TemplateSyntaxError("'image' tag should be of the form {%% image self.photo max-320x200 %%} or {%% image self.photo max-320x200 as img %%}")


class ImageNode(template.Node):
    def __init__(self, image_var_name, filter_spec, output_var_name=None):
        self.image_var = template.Variable(image_var_name)
        self.filter, created = Filter.objects.get_or_create(spec=filter_spec)
        self.output_var_name = output_var_name

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
            rendition = Rendition(image=image, width=0, height=0)
            rendition.file.name = 'not-found'

        if self.output_var_name:
            # return the rendition object in the given variable
            context[self.output_var_name] = rendition
            return ''
        else:
            # render the rendition's image tag now
            return rendition.img_tag()
