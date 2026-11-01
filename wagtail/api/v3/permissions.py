import functools

from django.core.exceptions import PermissionDenied
from django.db.models import Q

from wagtail.models import Collection, CollectionViewRestriction
from wagtail.permissions import policy_registry


def require_any_permission(model, actions=("add", "change", "delete", "view")):
    """
    Decorator factory that gates a view behind authentication and any of the
    given permission actions for ``model``, looked up via ``policy_registry``.

    If ``model`` is a function, it will be called with the same arguments as the
    view function to allow dynamic model resolution based on request parameters.

    Usage::

        @router.get("/")
        @require_any_permission(Site, ["add", "change", "delete", "view"])
        def list_sites(request):
            ...
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            resolved_model = model
            if callable(model) and not isinstance(model, type):
                # Allow dynamic model resolution based on request parameters.
                resolved_model = model(request, *args, **kwargs)

            permission_policy = policy_registry.get_by_type(resolved_model)
            if not permission_policy.user_has_any_permission(request.user, actions):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def get_restricted_collection_ids(request):
    """
    Returns a set of collection IDs that are restricted for the given request.
    """
    restricted_root_collection_ids = {
        # Django adds ``<foreign_key>_id`` attributes dynamically.
        restriction.collection_id  # ty: ignore[unresolved-attribute]
        for restriction in CollectionViewRestriction.objects.all()
        if not restriction.accept_request(request)
    }

    if not restricted_root_collection_ids:
        return set()

    restricted_collection_paths = Collection.objects.filter(
        id__in=restricted_root_collection_ids
    ).values_list("path", flat=True)

    restricted_collection_filters = Q()
    for path in restricted_collection_paths:
        restricted_collection_filters |= Q(path__startswith=path)

    return set(
        Collection.objects.filter(restricted_collection_filters).values_list(
            "id", flat=True
        )
    )
