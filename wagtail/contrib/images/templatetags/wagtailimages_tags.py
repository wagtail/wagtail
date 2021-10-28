from django import template

from .wagtailimages import image, image_url


register = template.Library()

register.tag(name="image")(image)
register.simple_tag(image_url)
