import django
from django.template import loader


def get_related_model(rel):
    # In Django 1.7 and under, the related model is accessed by doing: rel.model
    # This was renamed in Django 1.8 to rel.related_model. rel.model now returns
    # the base model.
    if django.VERSION >= (1, 8):
        return rel.related_model
    else:
        return rel.model


def render_to_string(template_name, context=None, request=None, **kwargs):
    if django.VERSION >= (1, 8):
        return loader.render_to_string(
            template_name,
            context=context,
            request=request,
            **kwargs
        )
    else:
        # Backwards compatibility for Django 1.7 and below
        from django.template.context import RequestContext
        return loader.render_to_string(
            template_name,
            dictionary=context,
            context_instance=RequestContext(request),
            **kwargs
        )
