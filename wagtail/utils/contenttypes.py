# -*- coding: utf-8 -*-
import django
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def get_content_type_for_model(model):
    """
    A wrapper for ContentType.objects.get_for_model() that ensures
    model-specific ContentType objects are returned for proxy models, instead
    of that of the concrete model, and that model permissions are correctly
    associated with any newly created objects.
    """
    opts = model._meta
    if opts.proxy:
        try:
            # get_by_natural_key allows efficient retrieval without creating
            return ContentType.objects.get_by_natural_key(opts.app_label, opts.model_name)
        except ContentType.DoesNotExist:
            if django.VERSION >= (2, 3):  # version could change here
                raise ContentType.DoesNotExist(
                    "ContentType could not be found for model '{app_label}.{model_name}'. Try "
                    "runing makemigrations and migrate for the '{app_label}' app, then try again."
                    .format(app_label=opts.app_label, model_name=opts.model_name)
                )
            return create_content_type_for_proxy_model(model)
    return ContentType.objects.get_for_model(model, for_concrete_model=False)


def create_content_type_for_proxy_model(model):
    """
    Creates a ContentType object for the supplied proxy model, and updates
    any Permission objects to be associated with the newly created ContentType
    instead of the ContentType for the concrete model.
    """
    opts = model._meta
    assert opts.proxy

    # Using get_or_create to handle race conditions
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

        # cache the new ContentType for speedier future lookups
        ContentType.objects._add_to_cache(ContentType.objects.db, proxy_ctype)
    return proxy_ctype
