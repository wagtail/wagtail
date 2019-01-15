# -*- coding: utf-8 -*-

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def get_content_type_for_model(model):
    """
    A wrapper for ContentType.objects.get_for_model() with some special
    handling for proxy models to ensure a model-specific ContentType is
    returned, instead of that of the concrete model.
    """
    opts = model._meta
    if opts.proxy:
        try:
            return ContentType.objects.get_by_natural_key(opts.app_label, opts.model_name)
        except ContentType.DoesNotExist:
            return create_content_type_for_proxy_model(model)
    return ContentType.objects.get_for_model(model, for_concrete_model=False)


def create_content_type_for_proxy_model(model):
    """
    Creates a ContentType object for the supplied proxy model, and updates
    any Permission objects to be associated with the newly created ContentType
    instead of the concrete model ContentType.
    """
    opts = model._meta
    assert opts.proxy

    # Using get_or_create for race condition handling
    proxy_ctype, created = ContentType.objects.get_or_create(
        app_label=opts.app_label, model=opts.model_name
    )
    if created:
        permission_codenames = [
            '%s_%s' % (action, opts.model_name)
            for action in opts.default_permissions
        ]
        permissions_query = Q(codename__in=permission_codenames)
        for codename, name in opts.permissions:
            permissions_query = permissions_query | Q(codename=codename, name=name)

        concrete_ctype = ContentType.objects.get_for_model(model, for_concrete_model=True)

        Permission.objects.filter(
            permissions_query, content_type=concrete_ctype
        ).update(content_type=proxy_ctype)

    return proxy_ctype
