import functools

from django.core.exceptions import PermissionDenied

from wagtail.permission_policies import ModelPermissionPolicy


def require_any_permission(model, actions=("add", "change", "delete", "view")):
    """
    Decorator factory that gates a view behind authentication and any of the
    given permission actions for *model*, looked up via ``policies_registry``.

    Usage::

        @router.get("/")
        @require_any_permission(Site, ["add", "change", "delete", "view"])
        def list_sites(request):
            ...
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # FIXME: use the registry when it's implemented.
            # from wagtail.permissions import policies_registry
            # permission_policy = policies_registry.get(model)
            permission_policy = ModelPermissionPolicy(model)
            if not permission_policy.user_has_any_permission(request.user, actions):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
