from django.conf import settings
from django.contrib.admin.utils import quote
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from wagtail.admin import messages
from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.utils import get_latest_str, get_valid_next_url_from_request
from wagtail.admin.views.generic.base import BaseObjectMixin
from wagtail.models import Task, TaskState, WorkflowState


class BaseWorkflowFormView(BaseObjectMixin, View):
    """
    Shared functionality for views that need to render the modal form to collect extra details
    for a workflow task
    """

    redirect_url_name = None
    submit_url_name = None
    template_name = "wagtailadmin/shared/workflow_action_modal.html"

    def setup(self, request, *args, action_name, task_state_id, **kwargs):
        super().setup(request, *args, **kwargs)
        self.action_name = action_name
        self.task_state_id = task_state_id
        self.redirect_url = self.get_redirect_url()
        self.task_state = self.get_task_state()
        self.task = self.get_task()
        self.form_class = self.get_form_class()

    def get_redirect_url(self):
        next_url = get_valid_next_url_from_request(self.request)
        if next_url:
            return next_url
        return reverse(self.redirect_url_name, args=(quote(self.object.pk),))

    def get_task_state(self):
        return get_object_or_404(TaskState, id=self.task_state_id).specific

    def get_task(self):
        return self.task_state.task.specific

    def get_form_class(self):
        return self.task.get_form_for_action(self.action_name)

    def get_template_names(self):
        if template := self.task.get_template_for_action(self.action_name):
            return [template]
        return [self.template_name]

    def add_not_in_moderation_error(self):
        messages.error(
            self.request,
            _("The %(model_name)s '%(title)s' is not currently awaiting moderation.")
            % {
                "model_name": self.model._meta.verbose_name,
                "title": get_latest_str(self.object),
            },
        )

    def check_action(self):
        actions = self.task.get_actions(self.object, self.request.user)
        self.action_verbose_name = ""
        action_available = False
        self.action_modal = False

        for name, verbose_name, modal in actions:
            if name == self.action_name:
                action_available = True
                if modal:
                    self.action_modal = True
                    # if two actions have the same name, use the verbose name
                    # of the one allowing modal data entry within the modal
                    self.action_verbose_name = verbose_name
        if not action_available:
            raise PermissionDenied

    def dispatch(self, request, *args, **kwargs):
        if not self.object.workflow_in_progress:
            self.add_not_in_moderation_error()
            return redirect(self.redirect_url)
        self.check_action()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_modal_form(request, self.form_class())

    def get_submit_url(self):
        return reverse(
            self.submit_url_name,
            args=(quote(self.object.pk), self.action_name, self.task_state.id),
        )

    def get_context_data(self, **kwargs):
        return {
            "object": self.object,
            "action": self.action_name,
            "action_verbose": self.action_verbose_name,
            "task_state": self.task_state,
            "submit_url": self.get_submit_url(),
            **kwargs,
        }

    def render_modal_form(self, request, form):
        return render_modal_workflow(
            request,
            self.get_template_names(),
            None,
            self.get_context_data(form=form),
            json_data={"step": "action"},
        )

    def render_modal_json(self, request, json_data):
        return render_modal_workflow(request, "", None, {}, json_data=json_data)


class WorkflowAction(BaseWorkflowFormView):
    """Provides a modal view to enter additional data for the specified workflow action on GET,
    or perform the specified action on POST"""

    def post(self, request, *args, **kwargs):
        if self.form_class:
            form = self.form_class(self.request.POST)
            if form.is_valid():
                self.redirect_url = (
                    self.task.on_action(
                        self.task_state,
                        self.request.user,
                        self.action_name,
                        **form.cleaned_data,
                    )
                    or self.redirect_url
                )
            elif (
                self.action_modal
                and self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            ):
                # show form errors
                return self.render_modal_form(self.request, form)
        else:
            self.redirect_url = (
                self.task.on_action(
                    self.task_state, self.request.user, self.action_name
                )
                or self.redirect_url
            )

        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return self.render_modal_json(
                self.request,
                {"step": "success", "redirect": self.redirect_url},
            )
        return redirect(self.redirect_url)


class CollectWorkflowActionData(BaseWorkflowFormView):
    """
    On GET, provides a modal view to enter additional data for the specified workflow action;
    on POST, return the validated form data back to the modal's caller via a JSON response, so that
    the calling view can subsequently perform the action as part of its own processing
    (for example, approving moderation while making an edit).
    """

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            return self.render_modal_json(
                request,
                {"step": "success", "cleaned_data": form.cleaned_data},
            )
        elif (
            self.action_modal
            and request.headers.get("x-requested-with") == "XMLHttpRequest"
        ):
            # show form errors
            return self.render_modal_form(request, form)
        return redirect(self.redirect_url)


class ConfirmWorkflowCancellation(BaseObjectMixin, View):
    template_name = "wagtailadmin/generic/confirm_workflow_cancellation.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.workflow_state = self.object.current_workflow_state

    def dispatch(self, request, *args, **kwargs):
        if not self.workflow_state or not getattr(
            settings, "WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH", True
        ):
            return render_modal_workflow(
                request,
                "",
                None,
                {},
                json_data={"step": "no_confirmation_needed"},
            )

        # This confirmation step is specific to the
        # `WAGTAIL_WORKFLOW_CANCEL_ON_PUBLISH` setting that happens when a user
        # publishes a page with a workflow in progress, which is different from
        # a "cancel" action on the task. So, we use `self.template_name`
        # directly and not make it customisable.
        return render_modal_workflow(
            request,
            self.template_name,
            None,
            self.get_context_data(),
            json_data={"step": "confirm"},
        )

    def get_context_data(self, **kwargs):
        return {
            "needs_changes": self.workflow_state.status
            == WorkflowState.STATUS_NEEDS_CHANGES,
            "task": self.workflow_state.current_task_state.task.name,
            "workflow": self.workflow_state.workflow.name,
            "model_opts": self.model_opts,
            **kwargs,
        }


class PreviewRevisionForTask(BaseObjectMixin, View):
    def setup(self, request, *args, task_id, **kwargs):
        super().setup(request, *args, **kwargs)
        self.task_id = task_id
        self.task = self.get_task()
        self.task_state = self.get_task_state()

    def get_task(self):
        return get_object_or_404(Task, id=self.task_id).specific

    def get_task_state(self):
        return TaskState.objects.filter(
            revision__base_content_type=self.object.get_base_content_type(),
            revision__object_id=self.pk,
            task=self.task,
            status=TaskState.STATUS_IN_PROGRESS,
        ).first()

    def add_error_message(self):
        messages.error(
            self.request,
            _(
                "The %(model_name)s '%(title)s' is not currently awaiting moderation in task '%(task_name)s'."
            )
            % {
                "model_name": self.model._meta.verbose_name,
                "title": get_latest_str(self.object),
                "task_name": self.task.name,
            },
        )

    def get(self, request, *args, **kwargs):
        if not self.task_state:
            self.add_error_message()
            return redirect("wagtailadmin_home")

        if not self.task.get_actions(self.object, request.user):
            raise PermissionDenied

        revision = self.task_state.revision
        object_to_view = revision.as_object()

        # TODO: provide workflow actions within this view

        return object_to_view.make_preview_request(
            request,
            object_to_view.default_preview_mode,
            extra_request_attrs={"revision_id": revision.id},
        )
