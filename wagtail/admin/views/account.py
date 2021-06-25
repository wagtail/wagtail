from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.db import transaction
from django.forms import Media
from django.http import Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, override
from django.views.decorators.debug import sensitive_post_parameters

from wagtail.admin.forms.account import (
    AvatarPreferencesForm, LocalePreferencesForm, NameEmailForm, NotificationPreferencesForm)
from wagtail.admin.forms.auth import LoginForm, PasswordChangeForm, PasswordResetForm
from wagtail.admin.localization import get_available_admin_languages, get_available_admin_time_zones
from wagtail.core import hooks
from wagtail.core.models import UserPagePermissionsProxy
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


# Tabs


class SettingsTab:
    def __init__(self, name, title, order=0):
        self.name = name
        self.title = title
        self.order = order


profile_tab = SettingsTab('profile', gettext_lazy("Profile"), order=100)
notifications_tab = SettingsTab('notifications', gettext_lazy("Notifications"), order=200)


# Panels

class BaseSettingsPanel:
    name = ''
    title = ''
    tab = profile_tab
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


class NameEmailSettingsPanel(BaseSettingsPanel):
    name = 'name_email'
    title = gettext_lazy('Name and Email')
    order = 100
    form_class = NameEmailForm


class AvatarSettingsPanel(BaseSettingsPanel):
    name = 'avatar'
    title = gettext_lazy('Profile picture')
    order = 300
    template_name = 'wagtailadmin/account/settings_panels/avatar.html'
    form_class = AvatarPreferencesForm
    form_object = 'profile'


class NotificationsSettingsPanel(BaseSettingsPanel):
    name = 'notifications'
    title = gettext_lazy('Notifications')
    tab = notifications_tab
    order = 100
    form_class = NotificationPreferencesForm
    form_object = 'profile'

    def is_active(self):
        # Hide the panel if the user can't edit or publish pages
        user_perms = UserPagePermissionsProxy(self.request.user)
        if not user_perms.can_edit_pages() and not user_perms.can_publish_pages():
            return False

        # Hide the panel if there are no notification preferences
        return self.get_form().fields


class LocaleSettingsPanel(BaseSettingsPanel):
    name = 'locale'
    title = gettext_lazy('Locale')
    order = 400
    form_class = LocalePreferencesForm
    form_object = 'profile'

    def is_active(self):
        return len(get_available_admin_languages()) > 1 or len(get_available_admin_time_zones()) > 1


class ChangePasswordPanel(BaseSettingsPanel):
    name = 'password'
    title = gettext_lazy('Password')
    order = 500
    form_class = PasswordChangeForm

    def is_active(self):
        return password_management_enabled() and self.user.has_usable_password()

    def get_form(self):
        # Note: don't bind the form unless a field is specified
        # This prevents the validation error from displaying if the user wishes to ignore this
        bind_form = False
        if self.request.method == 'POST':
            bind_form = any([
                self.request.POST.get(self.name + '-old_password'),
                self.request.POST.get(self.name + '-new_password1'),
                self.request.POST.get(self.name + '-new_password2'),
            ])

        if bind_form:
            return self.form_class(self.user, self.request.POST, prefix=self.name)
        else:
            return self.form_class(self.user, prefix=self.name)


# Views

@sensitive_post_parameters()
def account(request):
    # Fetch the user and profile objects once and pass into each panel
    # We need to use the same instances for all forms so they don't overwrite each other
    user = request.user
    profile = UserProfile.get_for_user(user)

    # Panels
    panels = [
        NameEmailSettingsPanel(request, user, profile),
        AvatarSettingsPanel(request, user, profile),
        NotificationsSettingsPanel(request, user, profile),
        LocaleSettingsPanel(request, user, profile),
        ChangePasswordPanel(request, user, profile),
    ]
    for fn in hooks.get_hooks('register_account_settings_panel'):
        panel = fn(request, user, profile)
        if panel and panel.is_active():
            panels.append(panel)

    panels = [panel for panel in panels if panel.is_active()]

    # Get tabs and order them
    tabs = list(set(panel.tab for panel in panels))
    tabs.sort(key=lambda tab: tab.order)

    # Get dict of tabs to ordered panels
    panels_by_tab = OrderedDict([(tab, []) for tab in tabs])
    for panel in panels:
        panels_by_tab[panel.tab].append(panel)
    for tab, tab_panels in panels_by_tab.items():
        tab_panels.sort(key=lambda panel: panel.order)

    panel_forms = [panel.get_form() for panel in panels]

    if request.method == 'POST':

        if all(form.is_valid() or not form.is_bound for form in panel_forms):
            with transaction.atomic():
                for form in panel_forms:
                    if form.is_bound:
                        form.save()

            # Prevent a password change from logging this user out
            update_session_auth_hash(request, user)

            # Override the language when creating the success message
            # If the user has changed their language in this request, the message should
            # be in the new language, not the existing one
            with override(profile.get_preferred_language()):
                messages.success(request, _("Your account settings have been changed successfully!"))

            return redirect('wagtailadmin_account')

    media = Media()
    for form in panel_forms:
        media += form.media

    # Menu items
    menu_items = []
    for fn in hooks.get_hooks('register_account_menu_item'):
        item = fn(request)
        if item:
            menu_items.append(item)

    return TemplateResponse(request, 'wagtailadmin/account/account.html', {
        'panels_by_tab': panels_by_tab,
        'menu_items': menu_items,
        'media': media,
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
