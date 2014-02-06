from django import template

register = template.Library()


@register.filter
def meta_description(model):
    try:
        return model.model_class()._meta.description
    except:
        return ""
