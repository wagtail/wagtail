from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import ugettext as _
from django.utils.translation import activate
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from wagtail.admin import forms
from wagtail.core import hooks
from wagtail.users.forms import (
    CurrentTimeZoneForm, EmailForm, NotificationPreferencesForm, PreferredLanguageForm)
from wagtail.users.models import UserProfile
from wagtail.utils.loading import get_custom_form


def get_user_login_form():
    form_setting = 'WAGTAILADMIN_USER_LOGIN_FORM'
    if hasattr(settings, form_setting):
        return get_custom_form(form_setting)
    else:
        return forms.LoginForm


# Helper functions to check password management settings to enable/disable views as appropriate.
# These are functions rather than class-level constants so that they can be overridden in tests
# by override_settings

def password_management_enabled():
    return getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True)


def password_reset_enabled():
    return getattr(settings, 'WAGTAIL_PASSWORD_RESET_ENABLED', password_management_enabled())


# Views

def account(request):
    items = []

    for fn in hooks.get_hooks('register_account_menu_item'):
        item = fn(request)
        if item:
            items.append(item)

    return render(request, 'wagtailadmin/account/account.html', {
        'items': items,
    })


def change_password(request):
    if not password_management_enabled():
        raise Http404

    can_change_password = request.user.has_usable_password()

    if can_change_password:
        if request.method == 'POST':
            form = PasswordChangeForm(request.user, request.POST)

            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)

                messages.success(request, _("Your password has been changed successfully!"))
                return redirect('wagtailadmin_account')
        else:
            form = PasswordChangeForm(request.user)
    else:
        form = None

    return render(request, 'wagtailadmin/account/change_password.html', {
        'form': form,
        'can_change_password': can_change_password,
    })


def change_email(request):
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, _("Your email has been changed successfully!"))
            return redirect('wagtailadmin_account')
    else:
        form = EmailForm(instance=request.user)

    return render(request, 'wagtailadmin/account/change_email.html', {
        'form': form,
    })


def _wrap_password_reset_view(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not password_reset_enabled():
            raise Http404
        return view_func(*args, **kwargs)
    return wrapper


password_reset = _wrap_password_reset_view(auth_views.password_reset)
password_reset_done = _wrap_password_reset_view(auth_views.password_reset_done)
password_reset_confirm = _wrap_password_reset_view(auth_views.password_reset_confirm)
password_reset_complete = _wrap_password_reset_view(auth_views.password_reset_complete)


def notification_preferences(request):
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=UserProfile.get_for_user(request.user))

        if form.is_valid():
            form.save()
            messages.success(request, _("Your preferences have been updated."))
            return redirect('wagtailadmin_account')
    else:
        form = NotificationPreferencesForm(instance=UserProfile.get_for_user(request.user))

    # quick-and-dirty catch-all in case the form has been rendered with no
    # fields, as the user has no customisable permissions
    if not form.fields:
        return redirect('wagtailadmin_account')

    return render(request, 'wagtailadmin/account/notification_preferences.html', {
        'form': form,
    })


def language_preferences(request):
    if request.method == 'POST':
        form = PreferredLanguageForm(request.POST, instance=UserProfile.get_for_user(request.user))

        if form.is_valid():
            user_profile = form.save()
            # This will set the language only for this request/thread
            # (so that the 'success' messages is in the right language)
            activate(user_profile.get_preferred_language())
            messages.success(request, _("Your preferences have been updated."))
            return redirect('wagtailadmin_account')
    else:
        form = PreferredLanguageForm(instance=UserProfile.get_for_user(request.user))

    return render(request, 'wagtailadmin/account/language_preferences.html', {
        'form': form,
    })


def current_time_zone(request):
    if request.method == 'POST':
        form = CurrentTimeZoneForm(request.POST, instance=UserProfile.get_for_user(request.user))

        if form.is_valid():
            form.save()
            messages.success(request, _("Your preferences have been updated."))
            return redirect('wagtailadmin_account')
    else:
        form = CurrentTimeZoneForm(instance=UserProfile.get_for_user(request.user))

    return render(request, 'wagtailadmin/account/current_time_zone.html', {
        'form': form,
    })


@sensitive_post_parameters()
@never_cache
def login(request):
    if request.user.is_authenticated and request.user.has_perm('wagtailadmin.access_admin'):
        return redirect('wagtailadmin_home')
    else:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return auth_views.login(
            request,
            template_name='wagtailadmin/login.html',
            authentication_form=get_user_login_form(),
            extra_context={
                'show_password_reset': password_reset_enabled(),
                'username_field': User._meta.get_field(
                    User.USERNAME_FIELD).verbose_name,
            },
        )


def logout(request):
    response = auth_views.logout(request, next_page='wagtailadmin_login')

    messages.success(request, _('You have been successfully logged out.'))
    # By default, logging out will generate a fresh sessionid cookie. We want to use the
    # absence of sessionid as an indication that front-end pages are being viewed by a
    # non-logged-in user and are therefore cacheable, so we forcibly delete the cookie here.
    response.delete_cookie(settings.SESSION_COOKIE_NAME,
                           domain=settings.SESSION_COOKIE_DOMAIN,
                           path=settings.SESSION_COOKIE_PATH)

    # HACK: pretend that the session hasn't been modified, so that SessionMiddleware
    # won't override the above and write a new cookie.
    request.session.modified = False

    return response
