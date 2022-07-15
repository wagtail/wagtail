from django.conf import settings
from django.contrib.admin.utils import quote
from django.forms import Media
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext as _

from wagtail import hooks
from wagtail.admin import messages
from wagtail.models import DraftStateMixin, Locale, TranslatableMixin


class HookResponseMixin:
    """
    A mixin for class-based views to run hooks by `hook_name`.
    """

    def run_hook(self, hook_name, *args, **kwargs):
        """
        Run the named hook, passing args and kwargs to each function registered under that hook name.
        If any return an HttpResponse, stop processing and return that response
        """
        for fn in hooks.get_hooks(hook_name):
            result = fn(*args, **kwargs)
            if hasattr(result, "status_code"):
                return result
        return None


class BeforeAfterHookMixin(HookResponseMixin):
    """
    A mixin for class-based views to support hooks like `before_edit_page` and
    `after_edit_page`, which are triggered during execution of some operation and
    can return a response to halt that operation and/or change the view response.
    """

    def run_before_hook(self):
        """
        Define how to run the hooks before the operation is executed.
        The `self.run_hook(hook_name, *args, **kwargs)` from HookResponseMixin
        can be utilised to call the hooks.

        If this method returns a response, the operation will be aborted and the
        hook response will be returned as the view response, skipping the default
        response.
        """
        return None

    def run_after_hook(self):
        """
        Define how to run the hooks after the operation is executed.
        The `self.run_hook(hook_name, *args, **kwargs)` from HookResponseMixin
        can be utilised to call the hooks.

        If this method returns a response, it will be returned as the view
        response immediately after the operation finishes, skipping the default
        response.
        """
        return None

    def dispatch(self, *args, **kwargs):
        hooks_result = self.run_before_hook()
        if hooks_result is not None:
            return hooks_result

        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)

        hooks_result = self.run_after_hook()
        if hooks_result is not None:
            return hooks_result

        return response


class LocaleMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.locale = self.get_locale()

    def get_locale(self):
        i18n_enabled = getattr(settings, "WAGTAIL_I18N_ENABLED", False)
        if hasattr(self, "model") and self.model:
            i18n_enabled = i18n_enabled and issubclass(self.model, TranslatableMixin)

        if not i18n_enabled:
            return None

        if hasattr(self, "object") and self.object:
            return self.object.locale

        selected_locale = self.request.GET.get("locale")
        if selected_locale:
            return get_object_or_404(Locale, language_code=selected_locale)
        return Locale.get_default()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.locale:
            return context

        context["locale"] = self.locale
        return context


class PanelMixin:
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.panel = self.get_panel()

    def get_panel(self):
        return None

    def get_bound_panel(self, form):
        if not self.panel:
            return None
        return self.panel.get_bound_panel(
            request=self.request, instance=form.instance, form=form
        )

    def get_form_class(self):
        if not self.panel:
            return super().get_form_class()
        return self.panel.get_form_class()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context.get("form")
        panel = self.get_bound_panel(form)

        media = context.get("media", Media())
        if form:
            media += form.media
        if panel:
            media += panel.media

        context.update(
            {
                "panel": panel,
                "media": media,
            }
        )

        return context


class RevisionsRevertMixin:
    revision_id_kwarg = "revision_id"
    revisions_revert_url_name = None

    def setup(self, request, *args, **kwargs):
        self.revision_id = kwargs.get(self.revision_id_kwarg)
        super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self._add_warning_message()
        return super().get(request, *args, **kwargs)

    def get_revisions_revert_url(self):
        return reverse(
            self.revisions_revert_url_name,
            args=[quote(self.object.pk), self.revision_id],
        )

    def get_warning_message(self):
        user_avatar = render_to_string(
            "wagtailadmin/shared/user_avatar.html", {"user": self.revision.user}
        )
        message_string = _(
            "You are viewing a previous version of this %(model_name)s from <b>%(created_at)s</b> by %(user)s"
        )
        message_data = {
            "model_name": capfirst(self.model._meta.verbose_name),
            "created_at": self.revision.created_at.strftime("%d %b %Y %H:%M"),
            "user": user_avatar,
        }
        message = mark_safe(message_string % message_data)
        return message

    def _add_warning_message(self):
        messages.warning(self.request, self.get_warning_message())

    def get_object(self, queryset=None):
        object = super().get_object(queryset)
        self.revision = get_object_or_404(object.revisions, id=self.revision_id)
        return self.revision.as_object()

    def save_instance(self):
        commit = not issubclass(self.model, DraftStateMixin)
        instance = self.form.save(commit=commit)

        self.has_content_changes = self.form.has_changed()

        self.new_revision = instance.save_revision(
            user=self.request.user,
            log_action=True,
            previous_revision=self.revision,
        )

        return instance

    def get_success_message(self):
        message = _(
            "{model_name} '{instance}' has been replaced with version from {timestamp}."
        )
        if self.action == "publish":
            message = _(
                "Version from {timestamp} of {model_name} '{instance}' has been published."
            )

        return message.format(
            model_name=capfirst(self.model._meta.verbose_name),
            instance=self.object,
            timestamp=self.revision.created_at.strftime("%d %b %Y %H:%M"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["revision"] = self.revision
        context["action_url"] = self.get_revisions_revert_url()
        return context
