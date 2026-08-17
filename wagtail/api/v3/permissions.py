import functools

from django.core.exceptions import PermissionDenied

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
