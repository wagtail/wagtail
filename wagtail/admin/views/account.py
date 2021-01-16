from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, override
from django.views.decorators.debug import sensitive_post_parameters

from wagtail.admin.forms.auth import LoginForm, PasswordResetForm
from wagtail.core import hooks
from wagtail.users.forms import (
    AvatarPreferencesForm, CurrentTimeZoneForm, EmailForm, NameForm, NotificationPreferencesForm,
    PreferredLanguageForm)
from wagtail.users.models import UserProfile
from wagtail.utils.loading import get_custom_form


def get_user_login_form():
    form_setting = 'WAGTAILADMIN_USER_LOGIN_FORM'
    if hasattr(settings, form_setting):
        return get_custom_form(form_setting)
    else:
        return LoginForm


# Helper functions to check password management settings to enable/disable views as appropriate.
# These are functions rather than class-level constants so that they can be overridden in tests
# by override_settings

def password_management_enabled():
    return getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True)


def email_management_enabled():
    return getattr(settings, 'WAGTAIL_EMAIL_MANAGEMENT_ENABLED', True)


def password_reset_enabled():
    return getattr(settings, 'WAGTAIL_PASSWORD_RESET_ENABLED', password_management_enabled())


# Panels

class BaseSettingsPanel:
    name = ''
    title = ''
    help_text = None
    template_name = 'wagtailadmin/account/settings_panels/base.html'
    form_class = None
    form_object = 'user'

    def __init__(self, request, user, profile):
        self.request = request
        self.user = user
        self.profile = profile

    def is_active(self):
        """
        Returns True to display the panel.
        """
        return True

    def get_form(self):
        """
        Returns an initialised form.
        """
        kwargs = {
            'instance': self.profile if self.form_object == 'profile' else self.user,
            'prefix': self.name
        }

        if self.request.method == 'POST':
            return self.form_class(self.request.POST, self.request.FILES, **kwargs)
        else:
            return self.form_class(**kwargs)

    def get_context_data(self):
        """
        Returns the template context to use when rendering the template.
        """
        return {
            'form': self.get_form()
        }

    def render(self):
        """
        Renders the panel using the template specified in .template_name and context from .get_context_data()
        """
        return render_to_string(self.template_name, self.get_context_data(), request=self.request)


class NameSettingsPanel(BaseSettingsPanel):
    name = 'name'
    title = gettext_lazy('Name')
    order = 100
    form_class = NameForm


class EmailSettingsPanel(BaseSettingsPanel):
    name = 'email'
    title = gettext_lazy('Email')
    order = 200
    form_class = EmailForm

    def is_active(self):
        return email_management_enabled()


class AvatarSettingsPanel(BaseSettingsPanel):
    name = 'avatar'
    title = gettext_lazy('Profile picture')
    order = 300
    template_name = 'wagtailadmin/account/settings_panels/avatar.html'
    form_class = AvatarPreferencesForm
    form_object = 'profile'


# Views

def account(request):
    # Fetch the user and profile objects once and pass into each panel
    # We need to use the same instances for all forms so they don't overwrite each other
    user = request.user
    profile = UserProfile.get_for_user(user)

    # Panels
    panels = [
        NameSettingsPanel(request, user, profile),
        EmailSettingsPanel(request, user, profile),
        AvatarSettingsPanel(request, user, profile),
    ]
    for fn in hooks.get_hooks('register_account_settings_panel'):
        panel = fn(request, user, profile)
        if panel and panel.is_active():
            panels.append(panel)

    panels = [panel for panel in panels if panel.is_active()]
    panels.sort(key=lambda panel: panel.order)

    if request.method == 'POST':
        panel_forms = [panel.get_form() for panel in panels]

        if all(form.is_valid() for form in panel_forms):
            with transaction.atomic():
                for form in panel_forms:
                    form.save()

            messages.success(request, _("Your account settings have been changed successfully!"))

            return redirect('wagtailadmin_account')

    # Menu items
    menu_items = []
    for fn in hooks.get_hooks('register_account_menu_item'):
        item = fn(request)
        if item:
            menu_items.append(item)

    return TemplateResponse(request, 'wagtailadmin/account/account.html', {
        'panels': panels,
        'menu_items': menu_items,
    })


@sensitive_post_parameters()
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

    return TemplateResponse(request, 'wagtailadmin/account/change_password.html', {
        'form': form,
        'can_change_password': can_change_password,
    })


class PasswordResetEnabledViewMixin:
    """
    Class based view mixin that disables the view if password reset is disabled by one of the following settings:
    - WAGTAIL_PASSWORD_RESET_ENABLED
    - WAGTAIL_PASSWORD_MANAGEMENT_ENABLED
    """
    def dispatch(self, *args, **kwargs):
        if not password_reset_enabled():
            raise Http404

        return super().dispatch(*args, **kwargs)


class PasswordResetView(PasswordResetEnabledViewMixin, auth_views.PasswordResetView):
    template_name = 'wagtailadmin/account/password_reset/form.html'
    email_template_name = 'wagtailadmin/account/password_reset/email.txt'
    subject_template_name = 'wagtailadmin/account/password_reset/email_subject.txt'
    form_class = PasswordResetForm
    success_url = reverse_lazy('wagtailadmin_password_reset_done')


class PasswordResetDoneView(PasswordResetEnabledViewMixin, auth_views.PasswordResetDoneView):
    template_name = 'wagtailadmin/account/password_reset/done.html'


class PasswordResetConfirmView(PasswordResetEnabledViewMixin, auth_views.PasswordResetConfirmView):
    template_name = 'wagtailadmin/account/password_reset/confirm.html'
    success_url = reverse_lazy('wagtailadmin_password_reset_complete')


class PasswordResetCompleteView(PasswordResetEnabledViewMixin, auth_views.PasswordResetCompleteView):
    template_name = 'wagtailadmin/account/password_reset/complete.html'


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

    return TemplateResponse(request, 'wagtailadmin/account/notification_preferences.html', {
        'form': form,
    })


def language_preferences(request):
    if request.method == 'POST':
        form = PreferredLanguageForm(request.POST, instance=UserProfile.get_for_user(request.user))

        if form.is_valid():
            user_profile = form.save()
            # This will set the language only for this request/thread
            # (so that the 'success' messages is in the right language)
            with override(user_profile.get_preferred_language()):
                messages.success(request, _("Your preferences have been updated."))
            return redirect('wagtailadmin_account')
    else:
        form = PreferredLanguageForm(instance=UserProfile.get_for_user(request.user))

    return TemplateResponse(request, 'wagtailadmin/account/language_preferences.html', {
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

    return TemplateResponse(request, 'wagtailadmin/account/current_time_zone.html', {
        'form': form,
    })


class LoginView(auth_views.LoginView):
    template_name = 'wagtailadmin/login.html'

    def get_success_url(self):
        return self.get_redirect_url() or reverse('wagtailadmin_home')

    def get(self, *args, **kwargs):
        # If user is already logged in, redirect them to the dashboard
        if self.request.user.is_authenticated and self.request.user.has_perm('wagtailadmin.access_admin'):
            return redirect(self.get_success_url())

        return super().get(*args, **kwargs)

    def get_form_class(self):
        return get_user_login_form()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['show_password_reset'] = password_reset_enabled()

        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['username_field'] = User._meta.get_field(User.USERNAME_FIELD).verbose_name

        return context


class LogoutView(auth_views.LogoutView):
    next_page = 'wagtailadmin_login'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        messages.success(self.request, _('You have been successfully logged out.'))
        # By default, logging out will generate a fresh sessionid cookie. We want to use the
        # absence of sessionid as an indication that front-end pages are being viewed by a
        # non-logged-in user and are therefore cacheable, so we forcibly delete the cookie here.
        response.delete_cookie(
            settings.SESSION_COOKIE_NAME,
            domain=settings.SESSION_COOKIE_DOMAIN,
            path=settings.SESSION_COOKIE_PATH
        )

        # HACK: pretend that the session hasn't been modified, so that SessionMiddleware
        # won't override the above and write a new cookie.
        self.request.session.modified = False

        return response
