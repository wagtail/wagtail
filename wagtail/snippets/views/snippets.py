from warnings import warn

from django.apps import apps
from django.contrib.admin.utils import quote
from django.core import checks
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.urls import path, re_path, reverse, reverse_lazy
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.panels import ObjectList, extract_panel_definitions_from_model_class
from wagtail.admin.ui.components import MediaContainer
from wagtail.admin.ui.side_panels import ChecksSidePanel, PreviewSidePanel
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    LiveStatusTagColumn,
    TitleColumn,
)
from wagtail.admin.views import generic
from wagtail.admin.views.generic import history, lock, workflow
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.generic.preview import (
    PreviewOnCreate,
    PreviewOnEdit,
    PreviewRevision,
)
from wagtail.admin.viewsets import viewsets
from wagtail.admin.viewsets.model import ModelViewSet, ModelViewSetGroup
from wagtail.admin.widgets.button import (
    BaseDropdownMenuButton,
    ButtonWithDropdown,
)
from wagtail.models import (
    DraftStateMixin,
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
    WorkflowMixin,
)
from wagtail.permissions import ModelPermissionPolicy
from wagtail.snippets.action_menu import SnippetActionMenu
from wagtail.snippets.models import SnippetAdminURLFinder, get_snippet_models
from wagtail.snippets.side_panels import SnippetStatusSidePanel
from wagtail.snippets.views.chooser import SnippetChooserViewSet
from wagtail.utils.deprecation import RemovedInWagtail70Warning


# == Helper functions ==
def get_snippet_model_from_url_params(app_name, model_name):
    """
    Retrieve a model from an app_label / model_name combo.
    Raise Http404 if the model is not a valid snippet type.
    """
    try:
        model = apps.get_model(app_name, model_name)
    except LookupError:
        raise Http404
    if model not in get_snippet_models():
        # don't allow people to hack the URL to edit content types that aren't registered as snippets
        raise Http404

    return model


# == Views ==


class ModelIndexView(generic.BaseListingView):
    page_title = gettext_lazy("Snippets")
    header_icon = "snippet"
    index_url_name = "wagtailsnippets:index"
    default_ordering = "name"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.snippet_types = self._get_snippet_types()

    def _get_snippet_types(self):
        return [
            {
                "name": capfirst(model._meta.verbose_name_plural),
                "count": model._default_manager.all().count(),
                "model": model,
                "url": url,
            }
            for model in get_snippet_models()
            if (url := self.get_list_url(model))
        ]

    def dispatch(self, request, *args, **kwargs):
        if not self.snippet_types:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_list_url(self, model):
        if model.snippet_viewset.permission_policy.user_has_any_permission(
            self.request.user,
            {"add", "change", "delete", "view"},
        ):
            return reverse(model.snippet_viewset.get_url_name("list"))

    def get_queryset(self):
        return None

    @cached_property
    def columns(self):
        return [
            TitleColumn(
                "name",
                label=_("Name"),
                get_url=lambda type: type["url"],
                sort_key="name",
            ),
            Column(
                "count",
                label=_("Instances"),
                sort_key="count",
            ),
        ]

    def get_context_data(self, **kwargs):
        reverse = self.ordering[0] == "-"

        if self.ordering in ["count", "-count"]:
            snippet_types = sorted(
                self.snippet_types,
                key=lambda type: type["count"],
                reverse=reverse,
            )
        else:
            snippet_types = sorted(
                self.snippet_types,
                key=lambda type: type["name"].lower(),
                reverse=reverse,
            )

        return super().get_context_data(object_list=snippet_types)

    def get_template_names(self):
        # We use the generic index template instead of model_index.html,
        # but we look for it anyway so users can customise this view's template
        # without having to override the entire view or the generic template.
        return [
            "wagtailsnippets/snippets/model_index.html",
            self.template_name,
        ]


class IndexView(generic.IndexViewOptionalFeaturesMixin, generic.IndexView):
    view_name = "list"

    def get_base_queryset(self):
        # Allow the queryset to be a callable that takes a request
        # so that it can be evaluated in the context of the request
        if callable(self.queryset):
            self.queryset = self.queryset(self.request)
        return super().get_base_queryset()

    @cached_property
    def columns(self):
        return [
            BulkActionsCheckboxColumn("bulk_actions", obj_type="snippet"),
            *super().columns,
        ]

    def _get_title_column(self, *args, **kwargs):
        return super()._get_title_column(
            *args,
            **kwargs,
            get_title_id=lambda instance: f"snippet_{quote(instance.pk)}_title",
        )

    def get_list_buttons(self, instance):
        more_buttons = self.get_list_more_buttons(instance)
        next_url = self.request.path
        list_buttons = []

        for hook in hooks.get_hooks("register_snippet_listing_buttons"):
            hook_buttons = hook(instance, self.request.user, next_url)
            for button in hook_buttons:
                if isinstance(button, BaseDropdownMenuButton):
                    # If the button is a dropdown menu, add it to the top-level
                    # because we do not support nested dropdowns
                    list_buttons.append(button)
                else:
                    # Otherwise, add it to the default "More" dropdown
                    more_buttons.append(button)

        # Pass the more_buttons to the construct hooks, as that's what contains
        # the default buttons and most buttons added via register_snippet_listing_buttons
        for hook in hooks.get_hooks("construct_snippet_listing_buttons"):
            try:
                hook(more_buttons, instance, self.request.user)
            except TypeError:
                warn(
                    "construct_snippet_listing_buttons hook no longer accepts a context argument",
                    RemovedInWagtail70Warning,
                    stacklevel=2,
                )
                hook(more_buttons, instance, self.request.user, {})

        if more_buttons:
            list_buttons.append(
                ButtonWithDropdown(
                    buttons=more_buttons,
                    icon_name="dots-horizontal",
                    attrs={
                        "aria-label": _("More options for '%(title)s'")
                        % {"title": str(instance)},
                    },
                )
            )

        return list_buttons


class CreateView(generic.CreateEditViewOptionalFeaturesMixin, generic.CreateView):
    view_name = "create"
    template_name = "wagtailsnippets/snippets/create.html"

    def run_before_hook(self):
        return self.run_hook("before_create_snippet", self.request, self.model)

    def run_after_hook(self):
        return self.run_hook("after_create_snippet", self.request, self.object)

    def _get_action_menu(self):
        return SnippetActionMenu(self.request, view=self.view_name, model=self.model)

    def get_side_panels(self):
        side_panels = [
            SnippetStatusSidePanel(
                self.form.instance,
                self.request,
                show_schedule_publishing_toggle=getattr(
                    self.form, "show_schedule_publishing_toggle", False
                ),
                locale=self.locale,
                translations=self.translations,
            )
        ]
        if self.preview_enabled and self.form.instance.is_previewable():
            side_panels.append(
                PreviewSidePanel(
                    self.form.instance, self.request, preview_url=self.get_preview_url()
                )
            )
            side_panels.append(ChecksSidePanel(self.form.instance, self.request))
        return MediaContainer(side_panels)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action_menu = self._get_action_menu()
        context["media"] += action_menu.media
        context["action_menu"] = action_menu
        return context


class CopyView(generic.CopyViewMixin, CreateView):
    pass


class EditView(generic.CreateEditViewOptionalFeaturesMixin, generic.EditView):
    view_name = "edit"
    template_name = "wagtailsnippets/snippets/edit.html"

    def run_before_hook(self):
        return self.run_hook("before_edit_snippet", self.request, self.object)

    def run_after_hook(self):
        return self.run_hook("after_edit_snippet", self.request, self.object)

    def _get_action_menu(self):
        return SnippetActionMenu(
            self.request,
            view=self.view_name,
            instance=self.object,
            locked_for_user=self.locked_for_user,
        )

    def get_side_panels(self):
        side_panels = [
            SnippetStatusSidePanel(
                self.object,
                self.request,
                show_schedule_publishing_toggle=getattr(
                    self.form, "show_schedule_publishing_toggle", False
                ),
                live_object=self.live_object,
                scheduled_object=self.live_object.get_scheduled_revision_as_object()
                if self.draftstate_enabled
                else None,
                locale=self.locale,
                translations=self.translations,
                usage_url=self.get_usage_url(),
                history_url=self.get_history_url(),
                last_updated_info=self.get_last_updated_info(),
            )
        ]
        if self.preview_enabled and self.object.is_previewable():
            side_panels.append(
                PreviewSidePanel(
                    self.object, self.request, preview_url=self.get_preview_url()
                )
            )
            side_panels.append(ChecksSidePanel(self.object, self.request))
        return MediaContainer(side_panels)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        action_menu = self._get_action_menu()
        context["media"] += action_menu.media
        context["action_menu"] = action_menu
        return context


class DeleteView(generic.DeleteView):
    view_name = "delete"

    def run_before_hook(self):
        return self.run_hook("before_delete_snippet", self.request, [self.object])

    def run_after_hook(self):
        return self.run_hook("after_delete_snippet", self.request, [self.object])


class UsageView(generic.UsageView):
    view_name = "usage"


class HistoryView(history.HistoryView):
    view_name = "history"


class InspectView(generic.InspectView):
    view_name = "inspect"


class PreviewOnCreateView(PreviewOnCreate):
    pass


class PreviewOnEditView(PreviewOnEdit):
    pass


class PreviewRevisionView(PermissionCheckedMixin, PreviewRevision):
    permission_required = "change"


class RevisionsCompareView(PermissionCheckedMixin, generic.RevisionsCompareView):
    permission_required = "change"


class UnpublishView(PermissionCheckedMixin, generic.UnpublishView):
    permission_required = "publish"


class RevisionsUnscheduleView(PermissionCheckedMixin, generic.RevisionsUnscheduleView):
    permission_required = "publish"


class LockView(PermissionCheckedMixin, lock.LockView):
    permission_required = "lock"

    def user_has_permission(self, permission):
        if self.request.user.is_superuser:
            return True

        if permission == self.permission_required and isinstance(
            self.object, WorkflowMixin
        ):
            current_workflow_task = self.object.current_workflow_task
            if current_workflow_task:
                return current_workflow_task.user_can_lock(
                    self.object, self.request.user
                )

        return super().user_has_permission(permission)


class UnlockView(PermissionCheckedMixin, lock.UnlockView):
    permission_required = "unlock"

    def user_has_permission(self, permission):
        if self.request.user.is_superuser:
            return True

        if permission == self.permission_required:
            # Allow unlocking even if the user does not have the 'unlock' permission
            # if they are the user who locked the object
            if self.object.locked_by_id == self.request.user.pk:
                return True

            if isinstance(self.object, WorkflowMixin):
                current_workflow_task = self.object.current_workflow_task
                if current_workflow_task:
                    return current_workflow_task.user_can_unlock(
                        self.object, self.request.user
                    )

        return super().user_has_permission(permission)


class WorkflowActionView(workflow.WorkflowAction):
    pass


class CollectWorkflowActionDataView(workflow.CollectWorkflowActionData):
    pass


class ConfirmWorkflowCancellationView(workflow.ConfirmWorkflowCancellation):
    pass


class WorkflowPreviewView(workflow.PreviewRevisionForTask):
    pass


class WorkflowHistoryView(PermissionCheckedMixin, history.WorkflowHistoryView):
    permission_required = "change"


class WorkflowHistoryDetailView(
    PermissionCheckedMixin, history.WorkflowHistoryDetailView
):
    permission_required = "change"


class SnippetViewSet(ModelViewSet):
    """
    A viewset that instantiates the admin views for snippets.

    All attributes and methods from
    :class:`~wagtail.admin.viewsets.model.ModelViewSet` are available.

    For more information on how to use this class,
    see :ref:`wagtailsnippets_custom_admin_views`.
    """

    #: The model class to be registered as a snippet with this viewset.
    model = None

    #: The number of items to display in the chooser view. Defaults to 10.
    chooser_per_page = 10

    #: The URL namespace to use for the admin views.
    #: If left unset, ``wagtailsnippets_{app_label}_{model_name}`` is used instead.
    #:
    #: **Deprecated** - the preferred attribute to customise is :attr:`~.ViewSet.url_namespace`.
    admin_url_namespace = None

    #: The base URL path to use for the admin views.
    #: If left unset, ``snippets/{app_label}/{model_name}`` is used instead.
    #:
    #: **Deprecated** - the preferred attribute to customise is :attr:`~.ViewSet.url_prefix`.
    base_url_path = None

    #: The URL namespace to use for the chooser admin views.
    #: If left unset, ``wagtailsnippetchoosers_{app_label}_{model_name}`` is used instead.
    chooser_admin_url_namespace = None

    #: The base URL path to use for the chooser admin views.
    #: If left unset, ``snippets/choose/{app_label}/{model_name}`` is used instead.
    chooser_base_url_path = None

    #: The view class to use for the index view; must be a subclass of ``wagtail.snippets.views.snippets.IndexView``.
    index_view_class = IndexView

    #: The view class to use for the create view; must be a subclass of ``wagtail.snippets.views.snippets.CreateView``.
    add_view_class = CreateView

    #: The view class to use for the copy view; must be a subclass of ``wagtail.snippet.views.snippets.CopyView``.
    copy_view_class = CopyView

    #: The view class to use for the edit view; must be a subclass of ``wagtail.snippets.views.snippets.EditView``.
    edit_view_class = EditView

    #: The view class to use for the delete view; must be a subclass of ``wagtail.snippets.views.snippets.DeleteView``.
    delete_view_class = DeleteView

    #: The view class to use for the usage view; must be a subclass of ``wagtail.snippets.views.snippets.UsageView``.
    usage_view_class = UsageView

    #: The view class to use for the history view; must be a subclass of ``wagtail.snippets.views.snippets.HistoryView``.
    history_view_class = HistoryView

    #: The view class to use for the inspect view; must be a subclass of ``wagtail.snippets.views.snippets.InspectView``.
    inspect_view_class = InspectView

    #: The view class to use for previewing revisions; must be a subclass of ``wagtail.snippets.views.snippets.PreviewRevisionView``.
    revisions_view_class = PreviewRevisionView

    #: The view class to use for comparing revisions; must be a subclass of ``wagtail.snippets.views.snippets.RevisionsCompareView``.
    revisions_compare_view_class = RevisionsCompareView

    #: The view class to use for unscheduling revisions; must be a subclass of ``wagtail.snippets.views.snippets.RevisionsUnscheduleView``.
    revisions_unschedule_view_class = RevisionsUnscheduleView

    #: The view class to use for unpublishing a snippet; must be a subclass of ``wagtail.snippets.views.snippets.UnpublishView``.
    unpublish_view_class = UnpublishView

    #: The view class to use for previewing on the create view; must be a subclass of ``wagtail.snippets.views.snippets.PreviewOnCreateView``.
    preview_on_add_view_class = PreviewOnCreateView

    #: The view class to use for previewing on the edit view; must be a subclass of ``wagtail.snippets.views.snippets.PreviewOnEditView``.
    preview_on_edit_view_class = PreviewOnEditView

    #: The view class to use for locking a snippet; must be a subclass of ``wagtail.snippets.views.snippets.LockView``.
    lock_view_class = LockView

    #: The view class to use for unlocking a snippet; must be a subclass of ``wagtail.snippets.views.snippets.UnlockView``.
    unlock_view_class = UnlockView

    #: The view class to use for performing a workflow action; must be a subclass of ``wagtail.snippets.views.snippets.WorkflowActionView``.
    workflow_action_view_class = WorkflowActionView

    #: The view class to use for performing a workflow action that returns the validated data in the response; must be a subclass of ``wagtail.snippets.views.snippets.CollectWorkflowActionDataView``.
    collect_workflow_action_data_view_class = CollectWorkflowActionDataView

    #: The view class to use for confirming the cancellation of a workflow; must be a subclass of ``wagtail.snippets.views.snippets.ConfirmWorkflowCancellationView``.
    confirm_workflow_cancellation_view_class = ConfirmWorkflowCancellationView

    #: The view class to use for previewing a revision for a specific task; must be a subclass of ``wagtail.snippets.views.snippets.WorkflowPreviewView``.
    workflow_preview_view_class = WorkflowPreviewView

    #: The view class to use for the workflow history view; must be a subclass of ``wagtail.snippets.views.snippets.WorkflowHistoryView``.
    workflow_history_view_class = WorkflowHistoryView

    #: The view class to use for the workflow history detail view; must be a subclass of ``wagtail.snippets.views.snippets.WorkflowHistoryDetailView``.
    workflow_history_detail_view_class = WorkflowHistoryDetailView

    #: The ViewSet class to use for the chooser views; must be a subclass of ``wagtail.snippets.views.chooser.SnippetChooserViewSet``.
    chooser_viewset_class = SnippetChooserViewSet

    #: The prefix of template names to look for when rendering the admin views.
    template_prefix = "wagtailsnippets/snippets/"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.model is None:
            raise ImproperlyConfigured(
                "SnippetViewSet must be passed a model or define a model attribute."
            )

        self.model_opts = self.model._meta
        self.app_label = self.model_opts.app_label
        self.model_name = self.model_opts.model_name

        self.preview_enabled = issubclass(self.model, PreviewableMixin)
        self.revision_enabled = issubclass(self.model, RevisionMixin)
        self.draftstate_enabled = issubclass(self.model, DraftStateMixin)
        self.workflow_enabled = issubclass(self.model, WorkflowMixin)
        self.locking_enabled = issubclass(self.model, LockableMixin)

        self.menu_item_is_registered = getattr(
            self, "menu_item_is_registered", bool(self.menu_hook)
        )

    @cached_property
    def url_prefix(self):
        # SnippetViewSet historically allows overriding the URL prefix via the
        # get_admin_base_path method or the admin_base_path attribute, so preserve that here
        return self.get_admin_base_path()

    @cached_property
    def url_namespace(self):
        # SnippetViewSet historically allows overriding the URL namespace via the
        # get_admin_url_namespace method or the admin_url_namespace attribute,
        # so preserve that here
        return self.get_admin_url_namespace()

    @property
    def revisions_revert_view_class(self):
        """
        The view class to use for reverting to a previous revision.

        By default, this class is generated by combining the edit view with
        ``wagtail.admin.views.generic.mixins.RevisionsRevertMixin``. As a result,
        this class must be a subclass of ``wagtail.snippets.views.snippets.EditView``
        and must handle the reversion correctly.
        """
        revisions_revert_view_class = type(
            "_RevisionsRevertView",
            (generic.RevisionsRevertMixin, self.edit_view_class),
            {"view_name": "revisions_revert"},
        )
        return revisions_revert_view_class

    @property
    def permission_policy(self):
        return ModelPermissionPolicy(self.model)

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "index_url_name": self.get_url_name("list"),
                "index_results_url_name": self.get_url_name("list_results"),
                "lock_url_name": self.get_url_name("lock"),
                "unlock_url_name": self.get_url_name("unlock"),
                "revisions_view_url_name": self.get_url_name("revisions_view"),
                "revisions_revert_url_name": self.get_url_name("revisions_revert"),
                "revisions_compare_url_name": self.get_url_name("revisions_compare"),
                "revisions_unschedule_url_name": self.get_url_name(
                    "revisions_unschedule"
                ),
                "unpublish_url_name": self.get_url_name("unpublish"),
                "breadcrumbs_items": self.breadcrumbs_items,
                **kwargs,
            }
        )

    def get_index_view_kwargs(self, **kwargs):
        return super().get_index_view_kwargs(
            queryset=self.get_queryset,
            **kwargs,
        )

    def get_add_view_kwargs(self, **kwargs):
        return super().get_add_view_kwargs(
            preview_url_name=self.get_url_name("preview_on_add"),
            **kwargs,
        )

    def get_copy_view_kwargs(self, **kwargs):
        return self.get_add_view_kwargs(**kwargs)

    def get_edit_view_kwargs(self, **kwargs):
        return super().get_edit_view_kwargs(
            preview_url_name=self.get_url_name("preview_on_edit"),
            workflow_history_url_name=self.get_url_name("workflow_history"),
            confirm_workflow_cancellation_url_name=self.get_url_name(
                "confirm_workflow_cancellation"
            ),
            **kwargs,
        )

    @property
    def revisions_view(self):
        return self.construct_view(self.revisions_view_class)

    @property
    def revisions_revert_view(self):
        return self.construct_view(
            self.revisions_revert_view_class,
            **self.get_edit_view_kwargs(),
        )

    @property
    def revisions_compare_view(self):
        return self.construct_view(
            self.revisions_compare_view_class,
            edit_handler=self._edit_handler,
            template_name=self.get_templates(
                "revisions_compare",
                fallback=self.revisions_compare_view_class.template_name,
            ),
        )

    @property
    def revisions_unschedule_view(self):
        return self.construct_view(
            self.revisions_unschedule_view_class,
            template_name=self.get_templates(
                "revisions_unschedule",
                fallback=self.revisions_unschedule_view_class.template_name,
            ),
        )

    @property
    def unpublish_view(self):
        return self.construct_view(
            self.unpublish_view_class,
            template_name=self.get_templates(
                "unpublish", fallback=self.unpublish_view_class.template_name
            ),
        )

    @property
    def preview_on_add_view(self):
        return self.construct_view(
            self.preview_on_add_view_class,
            form_class=self.get_form_class(),
        )

    @property
    def preview_on_edit_view(self):
        return self.construct_view(
            self.preview_on_edit_view_class,
            form_class=self.get_form_class(for_update=True),
        )

    @property
    def lock_view(self):
        return self.construct_view(
            self.lock_view_class,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def copy_view(self):
        return self.construct_view(self.copy_view_class, **self.get_copy_view_kwargs())

    @property
    def unlock_view(self):
        return self.construct_view(
            self.unlock_view_class,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def workflow_action_view(self):
        return self.construct_view(
            self.workflow_action_view_class,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("workflow_action"),
        )

    @property
    def collect_workflow_action_data_view(self):
        return self.construct_view(
            self.collect_workflow_action_data_view_class,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("collect_workflow_action_data"),
        )

    @property
    def confirm_workflow_cancellation_view(self):
        return self.construct_view(self.confirm_workflow_cancellation_view_class)

    @property
    def workflow_preview_view(self):
        return self.construct_view(self.workflow_preview_view_class)

    @property
    def workflow_history_view(self):
        return self.construct_view(
            self.workflow_history_view_class,
            template_name=self.get_templates(
                "workflow_history/index",
                fallback=self.workflow_history_view_class.template_name,
            ),
            workflow_history_detail_url_name=self.get_url_name(
                "workflow_history_detail"
            ),
        )

    @property
    def workflow_history_detail_view(self):
        return self.construct_view(
            self.workflow_history_detail_view_class,
            template_name=self.get_templates(
                "workflow_history/detail",
                fallback=self.workflow_history_detail_view_class.template_name,
            ),
            workflow_history_url_name=self.get_url_name("workflow_history"),
        )

    @property
    def redirect_to_usage_view(self):
        def redirect_to_usage(request, pk):
            warn(
                (
                    "%s's `/<pk>/usage/` usage view URL pattern has been "
                    "deprecated in favour of /usage/<pk>/."
                )
                % (self.__class__.__name__),
                category=RemovedInWagtail70Warning,
            )
            return redirect(self.get_url_name("usage"), pk, permanent=True)

        return redirect_to_usage

    @property
    def chooser_viewset(self):
        return self.chooser_viewset_class(
            self.get_chooser_admin_url_namespace(),
            model=self.model,
            url_prefix=self.get_chooser_admin_base_path(),
            icon=self.icon,
            per_page=self.chooser_per_page,
        )

    @cached_property
    def list_display(self):
        list_display = super().list_display.copy()
        if self.draftstate_enabled:
            list_display.append(LiveStatusTagColumn())
        return list_display

    @cached_property
    def icon(self):
        return self.get_icon()

    def get_icon(self):
        """
        Returns the icon to be used for the admin views.

        **Deprecated** - the preferred way to customise this is to define an ``icon`` property.
        """
        return "snippet"

    @cached_property
    def menu_label(self):
        return self.get_menu_label()

    def get_menu_label(self):
        """
        Returns the label text to be used for the menu item.

        **Deprecated** - the preferred way to customise this is to define a ``menu_label`` property.
        """
        return capfirst(self.model_opts.verbose_name_plural)

    @cached_property
    def menu_name(self):
        return self.get_menu_name()

    def get_menu_name(self):
        """
        Returns the name to be used for the menu item.

        **Deprecated** - the preferred way to customise this is to define a ``menu_name`` property.
        """
        return ""

    @cached_property
    def menu_icon(self):
        return self.get_menu_icon()

    def get_menu_icon(self):
        """
        Returns the icon to be used for the menu item.

        **Deprecated** - the preferred way to customise this is to define a ``menu_icon`` property.
        """
        return self.icon

    @cached_property
    def menu_order(self):
        return self.get_menu_order()

    def get_menu_order(self):
        """
        Returns the ordering number to be applied to the menu item.

        **Deprecated** - the preferred way to customise this is to define a ``menu_order`` property.
        """
        # By default, put it at the last item before Reports, whose order is 9000.
        return 8999

    def get_menu_item_is_registered(self):
        return self.menu_item_is_registered

    @cached_property
    def breadcrumbs_items(self):
        # Use reverse_lazy instead of reverse
        # because this will be passed to the view classes at startup
        return [
            {"url": reverse_lazy("wagtailadmin_home"), "label": _("Home")},
            {"url": reverse_lazy("wagtailsnippets:index"), "label": _("Snippets")},
        ]

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances to be shown on the index view.
        If ``None`` is returned (the default), the logic in
        ``index_view.get_base_queryset()`` will be used instead.
        """
        return None

    @cached_property
    def index_template_name(self):
        return self.get_index_template()

    def get_index_template(self):
        """
        Returns a template to be used when rendering ``index_view``. If a
        template is specified by the ``index_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define an ``index_template_name`` property.
        """
        return self.get_templates("index")

    @cached_property
    def index_results_template_name(self):
        return self.get_index_results_template()

    def get_index_results_template(self):
        """
        Returns a template to be used when rendering ``index_results_view``. If a
        template is specified by the ``index_results_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define an ``index_results_template_name`` property.
        """
        return self.get_templates("index_results")

    @cached_property
    def create_template_name(self):
        return self.get_create_template()

    def get_create_template(self):
        """
        Returns a template to be used when rendering ``add_view``. If a
        template is specified by the ``create_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define a ``create_template_name`` property.
        """
        return self.get_templates("create")

    @cached_property
    def edit_template_name(self):
        return self.get_edit_template()

    def get_edit_template(self):
        """
        Returns a template to be used when rendering ``edit_view``. If a
        template is specified by the ``edit_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define an ``edit_template_name`` property.
        """
        return self.get_templates("edit")

    @cached_property
    def delete_template_name(self):
        return self.get_delete_template()

    def get_delete_template(self):
        """
        Returns a template to be used when rendering ``delete_view``. If a
        template is specified by the ``delete_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define a ``delete_template_name`` property.
        """
        return self.get_templates("delete")

    @cached_property
    def history_template_name(self):
        """
        A template to be used when rendering ``history_view``.

        Default: if :attr:`template_prefix` is specified, a ``history.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``history_view_class.template_name`` will be used.
        """
        return self.get_history_template()

    def get_history_template(self):
        """
        Returns a template to be used when rendering ``history_view``. If a
        template is specified by the ``history_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define a ``history_template_name`` property.
        """
        return self.get_templates("history")

    @cached_property
    def inspect_template_name(self):
        """
        A template to be used when rendering ``inspect_view``.

        Default: if :attr:`template_prefix` is specified, an ``inspect.html``
        template in the prefix directory and its ``{app_label}/{model_name}/``
        or ``{app_label}/`` subdirectories will be used. Otherwise, the
        ``inspect_view_class.template_name`` will be used.
        """
        return self.get_inspect_template()

    def get_inspect_template(self):
        """
        Returns a template to be used when rendering ``inspect_view``. If a
        template is specified by the ``inspect_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.

        **Deprecated** - the preferred way to customise this is to define an ``inspect_template_name`` property.
        """
        return self.get_templates(
            "inspect", fallback=self.inspect_view_class.template_name
        )

    def get_admin_url_namespace(self):
        """
        Returns the URL namespace for the admin URLs for this model.

        **Deprecated** - the preferred way to customise this is to define a ``url_namespace`` property.
        """
        if self.admin_url_namespace:
            return self.admin_url_namespace
        return f"wagtailsnippets_{self.app_label}_{self.model_name}"

    def get_admin_base_path(self):
        """
        Returns the base path for the admin URLs for this model.
        The returned string must not begin or end with a slash.

        **Deprecated** - the preferred way to customise this is to define a ``url_prefix`` property.
        """
        if self.base_url_path:
            return self.base_url_path.strip().strip("/")
        return f"snippets/{self.app_label}/{self.model_name}"

    def get_chooser_admin_url_namespace(self):
        """Returns the URL namespace for the chooser admin URLs for this model."""
        if self.chooser_admin_url_namespace:
            return self.chooser_admin_url_namespace
        return f"wagtailsnippetchoosers_{self.app_label}_{self.model_name}"

    def get_chooser_admin_base_path(self):
        """
        Returns the base path for the chooser admin URLs for this model.
        The returned string must not begin or end with a slash.
        """
        if self.chooser_base_url_path:
            return self.chooser_base_url_path.strip().strip("/")
        return f"snippets/choose/{self.app_label}/{self.model_name}"

    @property
    def url_finder_class(self):
        return type(
            "_SnippetAdminURLFinder", (SnippetAdminURLFinder,), {"model": self.model}
        )

    def get_urlpatterns(self):
        urlpatterns = [
            path("", self.index_view, name="list"),
            path("results/", self.index_results_view, name="list_results"),
            path("add/", self.add_view, name="add"),
            path("edit/<str:pk>/", self.edit_view, name="edit"),
            path("delete/<str:pk>/", self.delete_view, name="delete"),
            path("usage/<str:pk>/", self.usage_view, name="usage"),
            path("history/<str:pk>/", self.history_view, name="history"),
            path(
                "history-results/<str:pk>/",
                self.history_results_view,
                name="history_results",
            ),
        ]

        if self.copy_view_enabled:
            urlpatterns += [path("copy/<str:pk>/", self.copy_view, name="copy")]

        if self.inspect_view_enabled:
            urlpatterns += [
                path("inspect/<str:pk>/", self.inspect_view, name="inspect")
            ]

        if self.preview_enabled:
            urlpatterns += [
                path("preview/", self.preview_on_add_view, name="preview_on_add"),
                path(
                    "preview/<str:pk>/",
                    self.preview_on_edit_view,
                    name="preview_on_edit",
                ),
            ]

        if self.revision_enabled:
            if self.preview_enabled:
                urlpatterns += [
                    path(
                        "history/<str:pk>/revisions/<int:revision_id>/view/",
                        self.revisions_view,
                        name="revisions_view",
                    )
                ]

            urlpatterns += [
                path(
                    "history/<str:pk>/revisions/<int:revision_id>/revert/",
                    self.revisions_revert_view,
                    name="revisions_revert",
                ),
                re_path(
                    r"history/(?P<pk>.+)/revisions/compare/(?P<revision_id_a>live|earliest|\d+)\.\.\.(?P<revision_id_b>live|latest|\d+)/$",
                    self.revisions_compare_view,
                    name="revisions_compare",
                ),
            ]

        if self.draftstate_enabled:
            urlpatterns += [
                path(
                    "history/<str:pk>/revisions/<int:revision_id>/unschedule/",
                    self.revisions_unschedule_view,
                    name="revisions_unschedule",
                ),
                path("unpublish/<str:pk>/", self.unpublish_view, name="unpublish"),
            ]

        if self.locking_enabled:
            urlpatterns += [
                path("lock/<str:pk>/", self.lock_view, name="lock"),
                path("unlock/<str:pk>/", self.unlock_view, name="unlock"),
            ]

        if self.workflow_enabled:
            urlpatterns += [
                path(
                    "workflow/action/<str:pk>/<slug:action_name>/<int:task_state_id>/",
                    self.workflow_action_view,
                    name="workflow_action",
                ),
                path(
                    "workflow/collect_action_data/<str:pk>/<slug:action_name>/<int:task_state_id>/",
                    self.collect_workflow_action_data_view,
                    name="collect_workflow_action_data",
                ),
                path(
                    "workflow/confirm_cancellation/<str:pk>/",
                    self.confirm_workflow_cancellation_view,
                    name="confirm_workflow_cancellation",
                ),
                path(
                    "workflow_history/<str:pk>/",
                    self.workflow_history_view,
                    name="workflow_history",
                ),
                path(
                    "workflow_history/<str:pk>/detail/<int:workflow_state_id>/",
                    self.workflow_history_detail_view,
                    name="workflow_history_detail",
                ),
            ]

            if self.preview_enabled:
                urlpatterns += [
                    path(
                        "workflow/preview/<str:pk>/<int:task_id>/",
                        self.workflow_preview_view,
                        name="workflow_preview",
                    ),
                ]

        # RemovedInWagtail70Warning: Remove legacy URL patterns
        return urlpatterns + self._legacy_urlpatterns

    @cached_property
    def _legacy_urlpatterns(self):
        return [
            # RemovedInWagtail70Warning: Remove legacy URL patterns
            # legacy URLs that could potentially collide if the pk matches one of the reserved names above
            # ('add', 'edit' etc) - redirect to the unambiguous version
            path("<str:pk>/", self.redirect_to_edit_view),
            path("<str:pk>/delete/", self.redirect_to_delete_view),
            path("<str:pk>/usage/", self.redirect_to_usage_view),
        ]

    def get_edit_handler(self):
        """
        Like :meth:`ModelViewSet.get_edit_handler()
        <wagtail.admin.viewsets.model.ModelViewSet.get_edit_handler>`,
        but falls back to extracting panel definitions from the model class
        if no edit handler is defined.
        """
        edit_handler = super().get_edit_handler()
        if edit_handler:
            return edit_handler

        exclude = self.get_exclude_form_fields()
        panels = extract_panel_definitions_from_model_class(self.model, exclude=exclude)
        edit_handler = ObjectList(panels)
        return edit_handler.bind_to_model(self.model)

    def register_chooser_viewset(self):
        viewsets.register(self.chooser_viewset)

    def register_model_check(self):
        def snippets_model_check(app_configs, **kwargs):
            return check_panels_in_model(self.model, "snippets")

        checks.register(snippets_model_check, "panels")

    def register_snippet_model(self):
        snippet_models = get_snippet_models()
        if self.model in snippet_models:
            raise ImproperlyConfigured(
                f"The {self.model.__name__} model is already registered as a snippet"
            )
        snippet_models.append(self.model)
        snippet_models.sort(key=lambda x: x._meta.verbose_name)

    def on_register(self):
        super().on_register()
        # For convenience, attach viewset to the model class to allow accessing
        # the configuration of a given model.
        self.model.snippet_viewset = self
        self.register_chooser_viewset()
        self.register_model_check()
        self.register_snippet_model()


class SnippetViewSetGroup(ModelViewSetGroup):
    """
    A container for grouping together multiple
    :class:`~wagtail.snippets.views.snippets.SnippetViewSet` instances.

    All attributes and methods from
    :class:`~wagtail.admin.viewsets.model.ModelViewSetGroup` are available.
    """

    def __init__(self):
        menu_item_is_registered = getattr(
            self, "menu_item_is_registered", bool(self.menu_hook)
        )
        # If the menu item is registered, mark all viewsets as such so that we can
        # hide the "Snippets" menu item if all snippets have their own menu items.
        for item in self.items:
            item.menu_item_is_registered = menu_item_is_registered

        # Call super() after setting menu_item_is_registered so that nested groups
        # can inherit the value.
        super().__init__()
