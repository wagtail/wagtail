import warnings
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _

from wagtail.admin import messages
from wagtail.admin.localization import get_localized_response
from wagtail.permission_policies.pages import PagePermissionPolicy
from wagtail.utils.deprecation import RemovedInWagtail60Warning


def users_with_page_permission(page, permission_type, include_superusers=True):
    warnings.warn(
        "users_with_page_permission() is deprecated. "
        "Use wagtail.permission_policies.pages.PagePermissionPolicy."
        "users_with_permission_for_instance() instead.",
        category=RemovedInWagtail60Warning,
        stacklevel=2,
    )
    return PagePermissionPolicy().users_with_permission_for_instance(
        permission_type, page, include_superusers
    )


def permission_denied(request):
    """Return a standard 'permission denied' response"""
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        raise PermissionDenied

    from wagtail.admin import messages

    messages.error(request, _("Sorry, you do not have permission to access this area."))
    return redirect("wagtailadmin_home")


def user_passes_test(test):
    """
    Given a test function that takes a user object and returns a boolean,
    return a view decorator that denies access to the user if the test returns false.
    """

    def decorator(view_func):
        # decorator takes the view function, and returns the view wrapped in
        # a permission check

        @wraps(view_func)
        def wrapped_view_func(request, *args, **kwargs):
            if test(request.user):
                # permission check succeeds; run the view function as normal
                return view_func(request, *args, **kwargs)
            else:
                # permission check failed
                return permission_denied(request)

        return wrapped_view_func

    return decorator


def permission_required(permission_name):
    """
    Replacement for django.contrib.auth.decorators.permission_required which returns a
    more meaningful 'permission denied' response than just redirecting to the login page.
    (The latter doesn't work anyway because Wagtail doesn't define LOGIN_URL...)
    """

    def test(user):
        return user.has_perm(permission_name)

    # user_passes_test constructs a decorator function specific to the above test function
    return user_passes_test(test)


def any_permission_required(*perms):
    """
    Decorator that accepts a list of permission names, and allows the user
    to pass if they have *any* of the permissions in the list
    """

    def test(user):
        for perm in perms:
            if user.has_perm(perm):
                return True

        return False

    return user_passes_test(test)


class PermissionPolicyChecker:
    """
    Provides a view decorator that enforces the given permission policy,
    returning the wagtailadmin 'permission denied' response if permission not granted
    """

    def __init__(self, policy):
        self.policy = policy

    def require(self, action):
        def test(user):
            return self.policy.user_has_permission(user, action)

        return user_passes_test(test)

    def require_any(self, *actions):
        def test(user):
            return self.policy.user_has_any_permission(user, actions)

        return user_passes_test(test)


def user_has_any_page_permission(user):
    """
    Check if a user has any permission to add, edit, or otherwise manage any
    page.
    """
    return PagePermissionPolicy().user_has_any_permission(
        user, {"add", "change", "publish", "bulk_delete", "lock", "unlock"}
    )


def reject_request(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        raise PermissionDenied

    # import redirect_to_login here to avoid circular imports on model files that import
    # wagtail.admin.auth, specifically where custom user models are involved
    from django.contrib.auth.views import redirect_to_login as auth_redirect_to_login

    return auth_redirect_to_login(
        request.get_full_path(), login_url=reverse("wagtailadmin_login")
    )


def require_admin_access(view_func):
    def decorated_view(request, *args, **kwargs):

        user = request.user

        if user.is_anonymous:
            return reject_request(request)

        if user.has_perms(["wagtailadmin.access_admin"]):
            try:
                return get_localized_response(user, view_func, request, *args, **kwargs)

            except PermissionDenied:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    raise

                return permission_denied(request)

        if not request.headers.get("x-requested-with") == "XMLHttpRequest":
            messages.error(request, _("You do not have permission to access the admin"))

        return reject_request(request)

    return decorated_view
