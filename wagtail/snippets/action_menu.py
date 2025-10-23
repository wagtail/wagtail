"""Handles rendering of the list of actions in the footer of the snippet create/edit views."""

from functools import lru_cache

from django.conf import settings
from django.contrib.admin.utils import quote
from django.forms import Media
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail.models import DraftStateMixin, LockableMixin, WorkflowMixin
from wagtail.snippets.permissions import get_permission_name


class ActionMenuItem(Component):
    """Defines an item in the actions drop-up on the snippet creation/edit view"""

    order = 100  # default order index if one is not specified on init
    template_name = "wagtailsnippets/snippets/action_menu/menu_item.html"

    label = ""
    name = None
    classname = ""
    icon_name = ""

    def __init__(self, order=None):
        if order is not None:
            self.order = order

    def is_shown(self, context):
        """
        Whether this action should be shown on this request; permission checks etc should go here.

        request = the current request object

        context = dictionary containing at least:
            'view' = 'create' or 'edit'
            'model' = the model of the snippet being created/edited
            'instance' (if view = 'edit') = the snippet being edited
        """
        return not context.get("locked_for_user")

    def get_context_data(self, parent_context):
        """Defines context for the template, overridable to use more data"""
        context = parent_context.copy()
        url = self.get_url(parent_context)

        instance = parent_context.get("instance")
        is_scheduled = (
            parent_context.get("draftstate_enabled")
            and instance
            and instance.go_live_at
        )

        context.update(
            {
                "label": self.label,
                "url": url,
                "name": self.name,
                "classname": self.classname,
                "icon_name": self.icon_name,
                "request": parent_context["request"],
                "is_scheduled": is_scheduled,
                "is_revision": parent_context["view"] == "revisions_revert",
            }
        )
        return context

    def get_url(self, parent_context):
        return None


class PublishMenuItem(ActionMenuItem):
    name = "action-publish"
    label = _("Publish")
    icon_name = "upload"
    template_name = "wagtailsnippets/snippets/action_menu/publish.html"

    def is_shown(self, context):
        publish_permission = get_permission_name("publish", context["model"])
        return context["request"].user.has_perm(publish_permission) and not context.get(
            "locked_for_user"
        )


class SubmitForModerationMenuItem(ActionMenuItem):
    name = "action-submit"
    label = _("Submit for moderation")
    icon_name = "resubmit"

    def is_shown(self, context):
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False

        if context.get("locked_for_user"):
            return False

        if context["view"] == "create":
            return context["model"].get_default_workflow() is not None

        return (
            context["view"] == "edit"
            and context["instance"].has_workflow
            and not context["instance"].workflow_in_progress
        )

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        instance = parent_context.get("instance")
        workflow_state = instance.current_workflow_state if instance else None

        if (
            workflow_state
            and workflow_state.status == workflow_state.STATUS_NEEDS_CHANGES
        ):
            context["label"] = _("Resubmit to %(task_name)s") % {
                "task_name": workflow_state.current_task_state.task.name
            }
        else:
            if instance:
                workflow = instance.get_workflow()
            else:
                workflow = context["model"].get_default_workflow()

            if workflow:
                context["label"] = _("Submit to %(workflow_name)s") % {
                    "workflow_name": workflow.name
                }
        return context


class WorkflowMenuItem(ActionMenuItem):
    template_name = "wagtailsnippets/snippets/action_menu/workflow_menu_item.html"

    def __init__(self, name, label, launch_modal, *args, **kwargs):
        self.name = name
        self.label = label
        self.launch_modal = launch_modal

        if kwargs.get("icon_name"):
            self.icon_name = kwargs.pop("icon_name")

        super().__init__(*args, **kwargs)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context["launch_modal"] = self.launch_modal
        return context

    def is_shown(self, context):
        return context["view"] == "edit" and not context.get("locked_for_user")

    def get_url(self, parent_context):
        instance = parent_context["instance"]
        url_name = instance.snippet_viewset.get_url_name("collect_workflow_action_data")
        return reverse(
            url_name,
            args=(
                quote(instance.pk),
                self.name,
                instance.current_workflow_task_state.pk,
            ),
        )


class RestartWorkflowMenuItem(ActionMenuItem):
    label = _("Restart workflow ")
    name = "action-restart-workflow"
    classname = "button--icon-flipped"
    icon_name = "login"

    def is_shown(self, context):
        if not getattr(settings, "WAGTAIL_WORKFLOW_ENABLED", True):
            return False
        if context["view"] != "edit":
            return False
        workflow_state = context["instance"].current_workflow_state
        return (
            not context.get("locked_for_user")
            and context["instance"].has_workflow
            and not context["instance"].workflow_in_progress
            and workflow_state
            and workflow_state.user_can_cancel(context["request"].user)
        )


class CancelWorkflowMenuItem(ActionMenuItem):
    label = _("Cancel workflow ")
    name = "action-cancel-workflow"
    icon_name = "error"

    def is_shown(self, context):
        if context["view"] != "edit":
            return False
        workflow_state = context["instance"].current_workflow_state
        return workflow_state and workflow_state.user_can_cancel(
            context["request"].user
        )


class UnpublishMenuItem(ActionMenuItem):
    label = _("Unpublish")
    name = "action-unpublish"
    icon_name = "download"

    def is_shown(self, context):
        if context.get("locked_for_user"):
            return False
        if context["view"] == "edit" and context["instance"].live:
            publish_permission = get_permission_name("publish", context["model"])
            return context["request"].user.has_perm(publish_permission)
        return False

    def get_url(self, context):
        instance = context["instance"]
        url_name = instance.snippet_viewset.get_url_name("unpublish")
        return reverse(url_name, args=[quote(instance.pk)])


class SaveMenuItem(ActionMenuItem):
    name = "action-save"
    label = _("Save")
    icon_name = "download"
    template_name = "wagtailsnippets/snippets/action_menu/save.html"


class LockedMenuItem(ActionMenuItem):
    name = "action-locked"
    label = _("Locked")
    template_name = "wagtailsnippets/snippets/action_menu/locked.html"

    def is_shown(self, context):
        return context.get("locked_for_user")


@lru_cache(maxsize=None)
def get_base_snippet_action_menu_items(model):
    """
    Retrieve the global list of menu items for the snippet action menu,
    which may then be customised on a per-request basis
    """
    menu_items = [
        SaveMenuItem(order=0),
    ]
    if issubclass(model, DraftStateMixin):
        menu_items += [
            UnpublishMenuItem(order=20),
            PublishMenuItem(order=30),
        ]
    if issubclass(model, WorkflowMixin):
        menu_items += [
            CancelWorkflowMenuItem(order=40),
            RestartWorkflowMenuItem(order=50),
            SubmitForModerationMenuItem(order=60),
        ]
    if issubclass(model, LockableMixin):
        menu_items.append(LockedMenuItem(order=10000))

    for hook in hooks.get_hooks("register_snippet_action_menu_item"):
        action_menu_item = hook(model)
        if action_menu_item:
            menu_items.append(action_menu_item)

    return menu_items


class SnippetActionMenu:
    template = "wagtailsnippets/snippets/action_menu/menu.html"

    def __init__(self, request, **kwargs):
        self.request = request
        self.context = kwargs
        self.context["request"] = request
        instance = self.context.get("instance")

        if instance:
            self.context["model"] = type(instance)

        self.context["draftstate_enabled"] = issubclass(
            self.context["model"], DraftStateMixin
        )

        self.menu_items = [
            menu_item
            for menu_item in get_base_snippet_action_menu_items(self.context["model"])
            if menu_item.is_shown(self.context)
        ]

        if instance and isinstance(instance, WorkflowMixin):
            task = instance.current_workflow_task
            current_workflow_state = instance.current_workflow_state
            is_final_task = (
                current_workflow_state and current_workflow_state.is_at_final_task
            )
            if task:
                actions = task.get_actions(instance, request.user)
                for name, label, launch_modal in actions:
                    icon_name = "edit"
                    if name == "approve":
                        if is_final_task and not getattr(
                            settings,
                            "WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT",
                            False,
                        ):
                            label = _("%(label)s and Publish") % {"label": label}
                        icon_name = "success"

                    item = WorkflowMenuItem(
                        name, label, launch_modal, icon_name=icon_name
                    )

                    if item.is_shown(self.context):
                        self.menu_items.append(item)

        self.menu_items.sort(key=lambda item: item.order)

        for hook in hooks.get_hooks("construct_snippet_action_menu"):
            hook(self.menu_items, self.request, self.context)

        try:
            self.default_item = self.menu_items.pop(0)
        except IndexError:
            self.default_item = None

    def render_html(self):
        if not self.default_item:
            return ""

        rendered_menu_items = [
            menu_item.render_html(self.context) for menu_item in self.menu_items
        ]
        rendered_default_item = self.default_item.render_html(self.context)

        return render_to_string(
            self.template,
            {
                "default_menu_item": rendered_default_item,
                "show_menu": bool(self.menu_items),
                "rendered_menu_items": rendered_menu_items,
            },
            request=self.request,
        )

    @cached_property
    def media(self):
        media = self.default_item.media if self.default_item else Media()
        for item in self.menu_items:
            media += item.media
        return media
