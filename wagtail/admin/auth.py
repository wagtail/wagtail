import types
from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import override as override_tz
from django.utils.translation import gettext as _
from django.utils.translation import override

from wagtail.admin import messages
from wagtail.log_actions import LogContext
from wagtail.permissions import page_permission_policy


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
    return page_permission_policy.user_has_any_permission(
        user, {"add", "change", "publish", "bulk_delete", "lock", "unlock"}
    )


def reject_request(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        raise PermissionDenied

    # import redirect_to_login here to avoid circular imports on model files that import
    # wagtail.admin.auth, specifically where custom user models are involved
    from django.contrib.auth.views import redirect_to_login as auth_redirect_to_login

    login_url = getattr(
        settings, "WAGTAILADMIN_LOGIN_URL", reverse("wagtailadmin_login")
    )

    return auth_redirect_to_login(request.get_full_path(), login_url=login_url)


def require_admin_access(view_func):
    def decorated_view(request, *args, **kwargs):
        user = request.user

        if user.is_anonymous:
            return reject_request(request)

        if user.has_perms(["wagtailadmin.access_admin"]):
            try:
                preferred_language = None
                if hasattr(user, "wagtail_userprofile"):
                    preferred_language = (
                        user.wagtail_userprofile.get_preferred_language()
                    )
                    time_zone = user.wagtail_userprofile.get_current_time_zone()
                else:
                    time_zone = settings.TIME_ZONE
                with override_tz(time_zone), LogContext(user=user):
                    if preferred_language:
                        with override(preferred_language):
                            response = view_func(request, *args, **kwargs)
                    else:
                        response = view_func(request, *args, **kwargs)

                    if hasattr(response, "render"):
                        # If the response has a render() method, Django treats it
                        # like a TemplateResponse, so we should do the same
                        # In this case, we need to guarantee that when the TemplateResponse
                        # is rendered, it is done within the override context manager
                        # or the user preferred_language/timezone will not be used
                        # (this could be replaced with simply rendering the TemplateResponse
                        # for simplicity but this does remove some of its middleware modification
                        # potential)
                        render = response.render

                        def overridden_render(response):
                            with override_tz(time_zone):
                                if preferred_language:
                                    with override(preferred_language):
                                        return render()
                                return render()

                        response.render = types.MethodType(overridden_render, response)
                        # decorate the response render method with the override context manager
                    return response

            except PermissionDenied:
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    raise

                return permission_denied(request)

        if not request.headers.get("x-requested-with") == "XMLHttpRequest":
            messages.error(request, _("You do not have permission to access the admin"))

        return reject_request(request)

    return decorated_view
