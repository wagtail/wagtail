# -*- coding: utf-8 -*-
import django
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

"""
This module is a temporary measure to help support proxy models throughout
Wagtail, by ensuring each has it's own ``ContentType``, and that ``Permission``
objects are correctly associated with any newly created ``ContentType`` objects
(rather than that of the concrete model).

Once Wagtail reaches a point where it supports only Django versions >= 2.2,
this module should be removed, and the wider project updated to use the
following:

- ``ContentType.objects.get_for_model(model, for_concrete_model=False)``
- ``ContentType.objects.get_for_models(*models, for_concrete_models=False)``
"""

manager = ContentType.objects
db = ContentType.objects.db


def get_for_model(model):
    """
    An alternative to ContentType.objects.get_for_model() that ensures
    model-specific content types are always returned for proxy models.
    """
    opts = model._meta
    try:
        # get_by_natural_key allows efficient retrieval without creating
        ct = manager.get_by_natural_key(opts.app_label, opts.model_name)
    except ContentType.DoesNotExist:
        return create_for_model(model)
    else:
        return ct


def get_for_models(*models):
    """
    An alternative to ContentType.objects.get_for_models() that ensures
    model-specific content types are always returned for proxy models.
    """
    results = {}
    # Mapping of opts:model for any objects not found in the cache
    not_found = {}
    # This will be used to query the db for objects not found in the cache
    contenttypes_q = Q()

    for model in set(models):
        opts = model._meta
        try:
            ct = manager._get_from_cache(opts)
        except KeyError:
            not_found[opts] = model
            contenttypes_q |= Q(app_label=opts.app_label, model=opts.model_name)
        else:
            results[model] = ct
    if not_found:
        # Lookup required content types from the DB.
        for ct in manager.all().filter(contenttypes_q):
            model = not_found.pop(ct.model_class()._meta)
            manager._add_to_cache(db, ct)
            results[model] = ct
    # Create content types that weren't in the cache or DB.
    for opts, model in not_found.items():
        results[model] = create_for_model(model)
    return results


def create_for_model(model):
    """
    Creates and returns a ``ContentType`` object for the provided ``model``. If
    the model happens to be a proxy model, any related ``Permission`` objects
    will be correctly associated with the new object, matching the approach
    taken by Django itself from 2.2.
    """
    opts = model._meta
    # get_or_create() used her to handle potential race conditions
    content_type, created = manager.get_or_create(
        app_label=opts.app_label, model=opts.model_name
    )
    if created and opts.proxy and django.VERSION < (2, 2):
        # To avoid any consistency/compatibilty issues, the approach below
        # matches that taken by Django in `0011_update_proxy_permissions.py` in
        # https://github.com/django/django/commit/181fb60159e54d442d3610f4afba6f066a6dac05,
        default_permissions_codenames = [
            '%s_%s' % (action, opts.model_name)
            for action in opts.default_permissions
        ]
        permissions_query = Q(codename__in=default_permissions_codenames)
        for codename, name in opts.permissions:
            permissions_query = permissions_query | Q(codename=codename, name=name)

        concrete_content_type = manager.get_for_model(model, for_concrete_model=True)

        Permission.objects.filter(
            permissions_query, content_type=concrete_content_type
        ).update(content_type=content_type)

    manager._add_to_cache(db, content_type)
    return content_type
