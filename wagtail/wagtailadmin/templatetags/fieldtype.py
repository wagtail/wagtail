from django import template

from wagtail.wagtailcore.util import camelcase_to_underscore

register = template.Library()

@register.filter
def fieldtype(bound_field):
	try:
		return camelcase_to_underscore(bound_field.field.__class__.__name__)
	except AttributeError:
		return ""
    
