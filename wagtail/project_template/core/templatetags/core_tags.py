from django import template
from django.conf import settings

register = template.Library()


# Return the model name/"content type" as a string e.g BlogPage, NewsListingPage.
# Can be used with "slugify" to create CSS-friendly classnames
# Usage: {% verbatim %}{{ self|content_type|slugify }}{% endverbatim %}
@register.filter
def content_type(model):
    return model.__class__.__name__
