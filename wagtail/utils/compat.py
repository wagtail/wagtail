import warnings

from django.template import loader

from wagtail.utils.deprecation import RemovedInWagtail16Warning


def get_related_model(rel):
    warnings.warn(
        'wagtail.utils.compat.get_related_model(rel) is deprecated. '
        'Use rel.related_model instead',
        RemovedInWagtail16Warning, stacklevel=2
    )
    return rel.related_model


def get_related_parent_model(rel):
    warnings.warn(
        'wagtail.utils.compat.get_related_parent_model(rel) is deprecated. '
        'Use rel.model instead',
        RemovedInWagtail16Warning, stacklevel=2
    )
    return rel.model


def render_to_string(template_name, context=None, request=None, **kwargs):
    warnings.warn(
        'wagtail.utils.compat.render_to_string is deprecated. '
        'Use django.template.loader.render_to_string instead',
        RemovedInWagtail16Warning, stacklevel=2
    )
    return loader.render_to_string(
        template_name,
        context=context,
        request=request,
        **kwargs
    )
