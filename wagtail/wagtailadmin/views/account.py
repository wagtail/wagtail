from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.views import logout as auth_logout, login as auth_login
from django.utils.translation import ugettext as _ 
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from wagtail.wagtailadmin import forms
from wagtail.wagtailusers.forms import NotificationPreferencesForm
from wagtail.wagtailusers.models import UserProfile
from wagtail.wagtailcore.models import UserPagePermissionsProxy


@permission_required('wagtailadmin.access_admin')
def account(request):
    user_perms = UserPagePermissionsProxy(request.user)
    show_notification_preferences = user_perms.can_edit_pages() or user_perms.can_publish_pages()

    return render(request, 'wagtailadmin/account/account.html', {
        'show_change_password': getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True) and request.user.has_usable_password(),
        'show_notification_preferences': show_notification_preferences
    })


@permission_required('wagtailadmin.access_admin')
def change_password(request):
    can_change_password = request.user.has_usable_password()

    if can_change_password:
        if request.POST:
            form = SetPasswordForm(request.user, request.POST)

            if form.is_valid():
                form.save()

                messages.success(request, _("Your password has been changed successfully!"))
                return redirect('wagtailadmin_account')
        else:
            form = SetPasswordForm(request.user)
    else:
        form = None

    return render(request, 'wagtailadmin/account/change_password.html', {
        'form': form,
        'can_change_password': can_change_password,
    })


@permission_required('wagtailadmin.access_admin')
def notification_preferences(request):

    if request.POST:
        form = NotificationPreferencesForm(request.POST, instance=UserProfile.get_for_user(request.user))

        if form.is_valid():
            form.save()
            messages.success(request, _("Your preferences have been updated successfully!"))
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


@sensitive_post_parameters()
@never_cache
def login(request):
    if request.user.is_authenticated():
        return redirect('wagtailadmin_home')
    else:
        return auth_login(request,
            template_name='wagtailadmin/login.html',
            authentication_form=forms.LoginForm,
            extra_context={
                'show_password_reset': getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True),
            },
        )


def logout(request):
    response = auth_logout(request, next_page = 'wagtailadmin_login')

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
