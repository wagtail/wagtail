from django.conf import settings
from django.shortcuts import render, redirect
from wagtail.wagtailadmin import messages
from django.contrib.auth.views import logout as auth_logout, login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse

from wagtail.wagtailadmin import forms
from wagtail.wagtailusers.forms import NotificationPreferencesForm
from wagtail.wagtailusers.models import UserProfile
from wagtail.wagtailcore.models import UserPagePermissionsProxy


def account(request):
    user_perms = UserPagePermissionsProxy(request.user)
    show_notification_preferences = user_perms.can_edit_pages() or user_perms.can_publish_pages()

    return render(request, 'wagtailadmin/account/account.html', {
        'show_notification_preferences': show_notification_preferences
    })


def edit(request):
    disable_password_fields = not getattr(
        settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True
    ) or not request.user.has_usable_password()

    if request.POST:
        form = forms.SingleUserEditForm(
            request.POST,
            instance=request.user,
            disable_password_fields=disable_password_fields
        )
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _("User '{0}' updated.").format(user), buttons=[
                messages.button(reverse('wagtailadmin_account_edit'), _('Edit'))
            ])
            return redirect('wagtailadmin_account')
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = forms.SingleUserEditForm(
            instance=request.user,
            disable_password_fields=disable_password_fields
        )

    return render(request, 'wagtailadmin/account/edit.html', {
        'user': request.user,
        'form': form,
        'disable_password_fields': disable_password_fields
    })


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
    if request.user.is_authenticated() and request.user.has_perm('wagtailadmin.access_admin'):
        return redirect('wagtailadmin_home')
    else:
        from django.contrib.auth import get_user_model
        return auth_login(request,
            template_name='wagtailadmin/login.html',
            authentication_form=forms.LoginForm,
            extra_context={
                'show_password_reset': getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True),
                'username_field': get_user_model().USERNAME_FIELD,
            },
        )


def logout(request):
    response = auth_logout(request, next_page='wagtailadmin_login')

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
