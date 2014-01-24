from django import template

from wagtail.wagtailcore.util import camelcase_to_underscore

register = template.Library()

@register.filter
def meta_description(model):
	try:
		return model.model_class()._meta.description
	except:
		return ""
    
