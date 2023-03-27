import django_filters
from django.apps import apps
from django.contrib.admin.utils import quote, unquote
from django.core import checks
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, re_path, reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail.admin.admin_url_finder import register_admin_url_finder
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.panels import get_edit_handler
from wagtail.admin.ui.tables import (
    BulkActionsCheckboxColumn,
    Column,
    DateColumn,
    InlineActionsTable,
    LiveStatusTagColumn,
    TitleColumn,
    UserColumn,
)
from wagtail.admin.views import generic
from wagtail.admin.views.generic import history, lock, workflow
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.generic.preview import (
    PreviewOnCreate,
    PreviewOnEdit,
    PreviewRevision,
)
from wagtail.admin.views.reports.base import ReportView
from wagtail.admin.viewsets import viewsets
from wagtail.admin.viewsets.base import ViewSet
from wagtail.log_actions import registry as log_registry
from wagtail.models import (
    DraftStateMixin,
    Locale,
    LockableMixin,
    PreviewableMixin,
    RevisionMixin,
    WorkflowMixin,
)
from wagtail.models.audit_log import ModelLogEntry
from wagtail.permissions import ModelPermissionPolicy
from wagtail.snippets.action_menu import SnippetActionMenu
from wagtail.snippets.models import SnippetAdminURLFinder, get_snippet_models
from wagtail.snippets.permissions import user_can_edit_snippet_type
from wagtail.snippets.side_panels import SnippetSidePanels
from wagtail.snippets.views.chooser import SnippetChooserViewSet


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


class ModelIndexView(generic.IndexView):
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
                "count": model.objects.all().count(),
                "model": model,
            }
            for model in get_snippet_models()
            if user_can_edit_snippet_type(self.request.user, model)
        ]

    def dispatch(self, request, *args, **kwargs):
        if not self.snippet_types:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_list_url(self, type):
        return reverse(type["model"].get_admin_url_namespace() + ":list")

    def get_queryset(self):
        return None

    def get_columns(self):
        return [
            TitleColumn(
                "name",
                label=_("Name"),
                get_url=self.get_list_url,
                sort_key="name",
            ),
            Column(
                "count",
                label=_("Instances"),
                sort_key="count",
            ),
        ]

    def get_context_data(self, **kwargs):
        ordering = self.get_ordering()
        reverse = ordering[0] == "-"

        if ordering in ["count", "-count"]:
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


class SnippetTitleColumn(TitleColumn):
    cell_template_name = "wagtailsnippets/snippets/tables/title_cell.html"


class IndexView(generic.IndexViewOptionalFeaturesMixin, generic.IndexView):
    viewset = None
    view_name = "list"
    index_results_url_name = None
    delete_url_name = None
    any_permission_required = ["add", "change", "delete"]
    page_kwarg = "p"
    # If true, returns just the 'results' include, for use in AJAX responses from search
    results_only = False
    table_class = InlineActionsTable

    def _get_title_column(self, field_name, column_class=SnippetTitleColumn, **kwargs):
        # Use SnippetTitleColumn class to use custom template
        # so that buttons from snippet_listing_buttons hook can be rendered
        return super()._get_title_column(field_name, column_class, **kwargs)

    def get_columns(self):
        return [
            BulkActionsCheckboxColumn("checkbox", accessor=lambda obj: obj),
            *super().get_columns(),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "model_opts": self.model._meta,
                "can_add_snippet": self.permission_policy.user_has_permission(
                    self.request.user, "add"
                ),
            }
        )

        if self.locale:
            context["translations"] = [
                {
                    "locale": locale,
                    "url": self.get_index_url() + "?locale=" + locale.language_code,
                }
                for locale in Locale.objects.all().exclude(id=self.locale.id)
            ]

        return context

    def get_template_names(self):
        if self.results_only:
            return self.viewset.get_index_results_template()
        else:
            return self.viewset.get_index_template()


class CreateView(generic.CreateEditViewOptionalFeaturesMixin, generic.CreateView):
    viewset = None
    view_name = "create"
    preview_url_name = None
    permission_required = "add"
    error_message = gettext_lazy("The snippet could not be created due to errors.")

    def run_before_hook(self):
        return self.run_hook("before_create_snippet", self.request, self.model)

    def run_after_hook(self):
        return self.run_hook("after_create_snippet", self.request, self.object)

    def get_panel(self):
        return get_edit_handler(self.model)

    def get_add_url(self):
        url = reverse(self.add_url_name)
        if self.locale:
            url += "?locale=" + self.locale.language_code
        return url

    def get_success_url(self):
        if self.draftstate_enabled and self.action != "publish":
            return super().get_success_url()

        # Make sure the redirect to the listing view uses the correct locale
        urlquery = ""
        if self.locale and self.object.locale is not Locale.get_default():
            urlquery = "?locale=" + self.object.locale.language_code

        return reverse(self.index_url_name) + urlquery

    def _get_action_menu(self):
        return SnippetActionMenu(self.request, view=self.view_name, model=self.model)

    def _get_initial_form_instance(self):
        instance = self.model()

        # Set locale of the new instance
        if self.locale:
            instance.locale = self.locale

        return instance

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "instance": self._get_initial_form_instance(),
            "for_user": self.request.user,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context.get("form")
        action_menu = self._get_action_menu()
        side_panels = SnippetSidePanels(
            self.request,
            self.model(),
            self,
            show_schedule_publishing_toggle=getattr(
                form, "show_schedule_publishing_toggle", False
            ),
        )
        media = context.get("media") + action_menu.media + side_panels.media

        context.update(
            {
                "model_opts": self.model._meta,
                "action_menu": action_menu,
                "side_panels": side_panels,
                "media": media,
            }
        )

        if self.locale:
            context["translations"] = [
                {
                    "locale": locale,
                    "url": reverse(self.add_url_name)
                    + "?locale="
                    + locale.language_code,
                }
                for locale in Locale.objects.all().exclude(id=self.locale.id)
            ]

        return context

    def get_template_names(self):
        return self.viewset.get_create_template()


class EditView(generic.CreateEditViewOptionalFeaturesMixin, generic.EditView):
    viewset = None
    view_name = "edit"
    history_url_name = None
    preview_url_name = None
    revisions_compare_url_name = None
    permission_required = "change"
    error_message = gettext_lazy("The snippet could not be saved due to errors.")

    def run_before_hook(self):
        return self.run_hook("before_edit_snippet", self.request, self.object)

    def run_after_hook(self):
        return self.run_hook("after_edit_snippet", self.request, self.object)

    def get_panel(self):
        return get_edit_handler(self.model)

    def get_history_url(self):
        return reverse(self.history_url_name, args=[quote(self.object.pk)])

    def _get_action_menu(self):
        return SnippetActionMenu(
            self.request,
            view=self.view_name,
            instance=self.object,
            locked_for_user=self.locked_for_user,
        )

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "for_user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = context.get("form")
        action_menu = self._get_action_menu()
        side_panels = SnippetSidePanels(
            self.request,
            self.object,
            self,
            show_schedule_publishing_toggle=getattr(
                form, "show_schedule_publishing_toggle", False
            ),
            live_object=self.live_object,
            scheduled_object=self.live_object.get_scheduled_revision_as_object()
            if self.draftstate_enabled
            else None,
        )
        media = context.get("media") + action_menu.media + side_panels.media

        context.update(
            {
                "model_opts": self.model._meta,
                "action_menu": action_menu,
                "side_panels": side_panels,
                "history_url": self.get_history_url(),
                "revisions_compare_url_name": self.revisions_compare_url_name,
                "media": media,
            }
        )

        if self.locale:
            context["translations"] = [
                {
                    "locale": translation.locale,
                    "url": reverse(
                        self.edit_url_name,
                        args=[quote(translation.pk)],
                    ),
                }
                for translation in self.object.get_translations().select_related(
                    "locale"
                )
            ]

        return context

    def get_template_names(self):
        return self.viewset.get_edit_template()


class DeleteView(generic.DeleteView):
    viewset = None
    view_name = "delete"
    page_title = gettext_lazy("Delete")
    permission_required = "delete"
    header_icon = "snippet"

    def run_before_hook(self):
        return self.run_hook("before_delete_snippet", self.request, [self.object])

    def run_after_hook(self):
        return self.run_hook("after_delete_snippet", self.request, [self.object])

    def get_success_message(self):
        return _("%(model_name)s '%(object)s' deleted.") % {
            "model_name": capfirst(self.model._meta.verbose_name),
            "object": self.object,
        }

    def get_template_names(self):
        return self.viewset.get_delete_template()


class UsageView(generic.UsageView):
    viewset = None
    view_name = "usage"
    permission_required = "change"

    def get_template_names(self):
        return self.viewset.get_templates("usage")


class SnippetHistoryReportFilterSet(WagtailFilterSet):
    action = django_filters.ChoiceFilter(
        label=_("Action"),
        choices=log_registry.get_choices,
    )
    user = django_filters.ModelChoiceFilter(
        label=_("User"),
        field_name="user",
        queryset=lambda request: ModelLogEntry.objects.all().get_users(),
    )
    timestamp = django_filters.DateFromToRangeFilter(
        label=_("Date"), widget=DateRangePickerWidget
    )

    class Meta:
        model = ModelLogEntry
        fields = ["action", "user", "timestamp"]


class ActionColumn(Column):
    cell_template_name = "wagtailsnippets/snippets/revisions/_actions.html"

    def __init__(self, *args, object=None, view=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.object = object
        self.view = view

    def get_cell_context_data(self, instance, parent_context):
        context = super().get_cell_context_data(instance, parent_context)
        context["revision_enabled"] = isinstance(self.object, RevisionMixin)
        context["draftstate_enabled"] = isinstance(self.object, DraftStateMixin)
        context["preview_enabled"] = isinstance(self.object, PreviewableMixin)
        context["can_publish"] = self.view.user_has_permission("publish")
        context["object"] = self.object
        context["view"] = self.view
        return context


class HistoryView(ReportView):
    viewset = None
    view_name = "history"
    index_url_name = None
    edit_url_name = None
    revisions_view_url_name = None
    revisions_revert_url_name = None
    revisions_compare_url_name = None
    revisions_unschedule_url_name = None
    any_permission_required = ["add", "change", "delete"]
    title = gettext_lazy("Snippet history")
    header_icon = "history"
    is_searchable = False
    paginate_by = 20
    filterset_class = SnippetHistoryReportFilterSet
    table_class = InlineActionsTable

    def setup(self, request, *args, pk, **kwargs):
        self.pk = pk
        self.object = self.get_object()
        super().setup(request, *args, **kwargs)

    def get_object(self):
        object = get_object_or_404(self.model, pk=unquote(self.pk))
        if isinstance(object, DraftStateMixin):
            return object.get_latest_revision_as_object()
        return object

    def get_page_subtitle(self):
        return str(self.object)

    def get_columns(self):
        return [
            ActionColumn(
                "message",
                object=self.object,
                view=self,
                classname="title",
                label=_("Action"),
            ),
            UserColumn("user", blank_display_name="system"),
            DateColumn("timestamp", label=_("Date")),
        ]

    def get_context_data(self, *args, object_list=None, **kwargs):
        context = super().get_context_data(*args, object_list=object_list, **kwargs)
        context["object"] = self.object
        context["subtitle"] = self.get_page_subtitle()
        context["model_opts"] = self.model._meta
        return context

    def get_queryset(self):
        return log_registry.get_logs_for_instance(self.object).select_related(
            "revision", "user", "user__wagtail_userprofile"
        )

    def get_template_names(self):
        return self.viewset.get_history_template()


class PreviewOnCreateView(PreviewOnCreate):
    viewset = None


class PreviewOnEditView(PreviewOnEdit):
    viewset = None


class PreviewRevisionView(PermissionCheckedMixin, PreviewRevision):
    viewset = None
    permission_required = "change"


class RevisionsCompareView(PermissionCheckedMixin, generic.RevisionsCompareView):
    viewset = None
    permission_required = "change"

    @property
    def edit_label(self):
        return _("Edit this %(model_name)s") % {
            "model_name": self.model._meta.verbose_name
        }

    @property
    def history_label(self):
        return _("%(model_name)s history") % {
            "model_name": self.model._meta.verbose_name
        }

    def get_template_names(self):
        return self.viewset.get_templates(
            "revisions_compare",
            fallback=self.template_name,
        )


class UnpublishView(PermissionCheckedMixin, generic.UnpublishView):
    viewset = None
    permission_required = "publish"

    def get_template_names(self):
        return self.viewset.get_templates(
            "unpublish",
            fallback=self.template_name,
        )


class RevisionsUnscheduleView(PermissionCheckedMixin, generic.RevisionsUnscheduleView):
    viewset = None
    permission_required = "publish"

    def get_template_names(self):
        return self.viewset.get_templates(
            "revisions_unschedule",
            fallback=self.template_name,
        )


class LockView(PermissionCheckedMixin, lock.LockView):
    viewset = None
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
    viewset = None
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
    viewset = None


class CollectWorkflowActionDataView(workflow.CollectWorkflowActionData):
    viewset = None


class ConfirmWorkflowCancellationView(workflow.ConfirmWorkflowCancellation):
    viewset = None


class WorkflowStatusView(PermissionCheckedMixin, workflow.WorkflowStatus):
    viewset = None
    permission_required = "change"


class WorkflowPreviewView(workflow.PreviewRevisionForTask):
    viewset = None


class WorkflowHistoryView(PermissionCheckedMixin, history.WorkflowHistoryView):
    viewset = None
    permission_required = "change"

    def get_template_names(self):
        return self.viewset.get_templates(
            "workflow_history/index",
            fallback=self.template_name,
        )


class WorkflowHistoryDetailView(
    PermissionCheckedMixin, history.WorkflowHistoryDetailView
):
    viewset = None
    permission_required = "change"

    def get_template_names(self):
        return self.viewset.get_templates(
            "workflow_history/detail",
            fallback=self.template_name,
        )


class SnippetViewSet(ViewSet):
    """
    A viewset that instantiates the admin views for snippets.
    """

    #: The icon to use across the admin for this snippet type.
    icon = "snippet"

    #: A subclass of ``wagtail.admin.filters.WagtailFilterSet``, which is a subclass of `django_filters.FilterSet <https://django-filter.readthedocs.io/en/stable/ref/filterset.html>`_. This will be passed to the ``filterset_class`` attribute of the index view.
    filterset_class = None

    #: A list or tuple, where each item is either:
    #:
    #: - The name of a field on the model;
    #: - The name of a callable or property on the model that accepts a single parameter for the model instance; or
    #: - An instance of the ``wagtail.admin.ui.tables.Column`` class.
    #:
    #: If the name refers to a database field, the ability to sort the listing by the database column will be offerred and the field's verbose name will be used as the column header.
    #:
    #: If the name refers to a callable or property, a ``admin_order_field`` attribute can be defined on it to point to the database column for sorting.
    #: A ``short_description`` attribute can also be defined on the callable or property to be used as the column header.
    #:
    #: This list will be passed to the ``list_display`` attribute of the index view.
    #: If left unset, the ``list_display`` attribute of the index view will be used instead, which by default is defined as ``["__str__", wagtail.admin.ui.tables.UpdatedAtColumn()]``.
    list_display = None

    #: A list or tuple, where each item is the name of model fields of type ``BooleanField``, ``CharField``, ``DateField``, ``DateTimeField``, ``IntegerField`` or ``ForeignKey``.
    #: Alternatively, it can also be a dictionary that maps a field name to a list of lookup expressions.
    #: This will be passed as django-filter's ``FilterSet.Meta.fields`` attribute. See `its documentation <https://django-filter.readthedocs.io/en/stable/guide/usage.html#generating-filters-with-meta-fields>`_ for more details.
    #: If ``filterset_class`` is set, this attribute will be ignored.
    list_filter = None

    #: The number of items to display per page in the index view. Defaults to 20.
    list_per_page = 20

    #: The number of items to display in the chooser view. Defaults to 10.
    chooser_per_page = 10

    #: The URL namespace to use for the admin views.
    #: If left unset, ``wagtailsnippets_{app_label}_{model_name}`` is used instead.
    admin_url_namespace = None

    #: The base URL path to use for the admin views.
    #: If left unset, ``snippets/{app_label}/{model_name}`` is used instead.
    base_url_path = None

    #: The URL namespace to use for the chooser admin views.
    #: If left unset, ``wagtailsnippetchoosers_{app_label}_{model_name}`` is used instead.
    chooser_admin_url_namespace = None

    #: The base URL path to use for the chooser admin views.
    #: If left unset, ``snippets/choose/{app_label}/{model_name}`` is used instead.
    chooser_base_url_path = None

    #: The view class to use for the index view; must be a subclass of ``wagtail.snippet.views.snippets.IndexView``.
    index_view_class = IndexView

    #: The view class to use for the create view; must be a subclass of ``wagtail.snippet.views.snippets.CreateView``.
    add_view_class = CreateView

    #: The view class to use for the edit view; must be a subclass of ``wagtail.snippet.views.snippets.EditView``.
    edit_view_class = EditView

    #: The view class to use for the delete view; must be a subclass of ``wagtail.snippet.views.snippets.DeleteView``.
    delete_view_class = DeleteView

    #: The view class to use for the usage view; must be a subclass of ``wagtail.snippet.views.snippets.UsageView``.
    usage_view_class = UsageView

    #: The view class to use for the history view; must be a subclass of ``wagtail.snippet.views.snippets.HistoryView``.
    history_view_class = HistoryView

    #: The view class to use for previewing revisions; must be a subclass of ``wagtail.snippet.views.snippets.PreviewRevisionView``.
    revisions_view_class = PreviewRevisionView

    #: The view class to use for comparing revisions; must be a subclass of ``wagtail.snippet.views.snippets.RevisionsCompareView``.
    revisions_compare_view_class = RevisionsCompareView

    #: The view class to use for unscheduling revisions; must be a subclass of ``wagtail.snippet.views.snippets.RevisionsUnscheduleView``.
    revisions_unschedule_view_class = RevisionsUnscheduleView

    #: The view class to use for unpublishing a snippet; must be a subclass of ``wagtail.snippet.views.snippets.UnpublishView``.
    unpublish_view_class = UnpublishView

    #: The view class to use for previewing on the create view; must be a subclass of ``wagtail.snippet.views.snippets.PreviewOnCreateView``.
    preview_on_add_view_class = PreviewOnCreateView

    #: The view class to use for previewing on the edit view; must be a subclass of ``wagtail.snippet.views.snippets.PreviewOnEditView``.
    preview_on_edit_view_class = PreviewOnEditView

    #: The view class to use for locking a snippet; must be a subclass of ``wagtail.snippet.views.snippets.LockView``.
    lock_view_class = LockView

    #: The view class to use for unlocking a snippet; must be a subclass of ``wagtail.snippet.views.snippets.UnlockView``.
    unlock_view_class = UnlockView

    #: The view class to use for performing a workflow action; must be a subclass of ``wagtail.snippet.views.snippets.WorkflowActionView``.
    workflow_action_view_class = WorkflowActionView

    #: The view class to use for performing a workflow action that returns the validated data in the response; must be a subclass of ``wagtail.snippet.views.snippets.CollectWorkflowActionDataView``.
    collect_workflow_action_data_view_class = CollectWorkflowActionDataView

    #: The view class to use for confirming the cancellation of a workflow; must be a subclass of ``wagtail.snippet.views.snippets.ConfirmWorkflowCancellationView``.
    confirm_workflow_cancellation_view_class = ConfirmWorkflowCancellationView

    #: The view class to use for rendering the workflow status modal; must be a subclass of ``wagtail.snippet.views.snippets.WorkflowStatusView``.
    workflow_status_view_class = WorkflowStatusView

    #: The view class to use for previewing a revision for a specific task; must be a subclass of ``wagtail.snippet.views.snippets.WorkflowPreviewView``.
    workflow_preview_view_class = WorkflowPreviewView

    #: The view class to use for the workflow history view; must be a subclass of ``wagtail.snippet.views.snippets.WorkflowHistoryView``.
    workflow_history_view_class = WorkflowHistoryView

    #: The view class to use for the workflow history detail view; must be a subclass of ``wagtail.snippet.views.snippets.WorkflowHistoryDetailView``.
    workflow_history_detail_view_class = WorkflowHistoryDetailView

    #: The ViewSet class to use for the chooser views; must be a subclass of ``wagtail.snippet.views.chooser.SnippetChooserViewSet``.
    chooser_viewset_class = SnippetChooserViewSet

    #: The template to use for the index view.
    index_template_name = ""

    #: The template to use for the results in the index view.
    index_results_template_name = ""

    #: The template to use for the create view.
    create_template_name = ""

    #: The template to use for the edit view.
    edit_template_name = ""

    #: The template to use for the delete view.
    delete_template_name = ""

    #: The template to use for the history view.
    history_template_name = ""

    def __init__(self, model, **kwargs):
        self.model = model
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name

        self.preview_enabled = issubclass(self.model, PreviewableMixin)
        self.revision_enabled = issubclass(self.model, RevisionMixin)
        self.draftstate_enabled = issubclass(self.model, DraftStateMixin)
        self.workflow_enabled = issubclass(self.model, WorkflowMixin)
        self.locking_enabled = issubclass(self.model, LockableMixin)

        super().__init__(
            name=self.get_admin_url_namespace(),
            url_prefix=self.get_admin_base_path(),
            **kwargs,
        )

        if not self.list_display:
            self.list_display = self.index_view_class.list_display.copy()
            if self.draftstate_enabled:
                self.list_display += [LiveStatusTagColumn()]

    @property
    def revisions_revert_view_class(self):
        """
        The view class to use for reverting to a previous revision.

        By default, this class is generated by combining the edit view with
        ``wagtail.admin.views.generic.mixins.RevisionsRevertMixin``. As a result,
        this class must be a subclass of ``wagtail.snippet.views.snippets.EditView``
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

    @property
    def index_view(self):
        return self.index_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            filterset_class=self.filterset_class,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            index_results_url_name=self.get_url_name("list_results"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            list_display=self.list_display,
            list_filter=self.list_filter,
            paginate_by=self.list_per_page,
        )

    @property
    def index_results_view(self):
        return self.index_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            filterset_class=self.filterset_class,
            permission_policy=self.permission_policy,
            results_only=True,
            index_url_name=self.get_url_name("list"),
            index_results_url_name=self.get_url_name("list_results"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            list_display=self.list_display,
            list_filter=self.list_filter,
            paginate_by=self.list_per_page,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            preview_url_name=self.get_url_name("preview_on_add"),
        )

    @property
    def edit_view(self):
        # Any parameters passed here must also be passed in revisions_revert_view.
        return self.edit_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
            lock_url_name=self.get_url_name("lock"),
            unlock_url_name=self.get_url_name("unlock"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
            workflow_history_url_name=self.get_url_name("workflow_history"),
            confirm_workflow_cancellation_url_name=self.get_url_name(
                "confirm_workflow_cancellation"
            ),
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            delete_url_name=self.get_url_name("delete"),
            usage_url_name=self.get_url_name("usage"),
        )

    @property
    def usage_view(self):
        return self.usage_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
        )

    @property
    def history_view(self):
        return self.history_view_class.as_view(
            viewset=self,
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            revisions_view_url_name=self.get_url_name("revisions_view"),
            revisions_revert_url_name=self.get_url_name("revisions_revert"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
        )

    @property
    def revisions_view(self):
        return self.revisions_view_class.as_view(
            viewset=self,
            model=self.model,
            permission_policy=self.permission_policy,
        )

    @property
    def revisions_revert_view(self):
        return self.revisions_revert_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
            lock_url_name=self.get_url_name("lock"),
            unlock_url_name=self.get_url_name("unlock"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
            revisions_revert_url_name=self.get_url_name("revisions_revert"),
            workflow_history_url_name=self.get_url_name("workflow_history"),
            confirm_workflow_cancellation_url_name=self.get_url_name(
                "confirm_workflow_cancellation"
            ),
        )

    @property
    def revisions_compare_view(self):
        return self.revisions_compare_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
        )

    @property
    def revisions_unschedule_view(self):
        return self.revisions_unschedule_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
        )

    @property
    def unpublish_view(self):
        return self.unpublish_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            unpublish_url_name=self.get_url_name("unpublish"),
            usage_url_name=self.get_url_name("usage"),
        )

    @property
    def preview_on_add_view(self):
        return self.preview_on_add_view_class.as_view(
            viewset=self,
            model=self.model,
        )

    @property
    def preview_on_edit_view(self):
        return self.preview_on_edit_view_class.as_view(
            viewset=self,
            model=self.model,
        )

    @property
    def lock_view(self):
        return self.lock_view_class.as_view(
            viewset=self,
            model=self.model,
            permission_policy=self.permission_policy,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def unlock_view(self):
        return self.unlock_view_class.as_view(
            viewset=self,
            model=self.model,
            permission_policy=self.permission_policy,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def workflow_action_view(self):
        return self.workflow_action_view_class.as_view(
            viewset=self,
            model=self.model,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("workflow_action"),
        )

    @property
    def collect_workflow_action_data_view(self):
        return self.collect_workflow_action_data_view_class.as_view(
            viewset=self,
            model=self.model,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("collect_workflow_action_data"),
        )

    @property
    def confirm_workflow_cancellation_view(self):
        return self.confirm_workflow_cancellation_view_class.as_view(
            viewset=self,
            model=self.model,
        )

    @property
    def workflow_status_view(self):
        return self.workflow_status_view_class.as_view(
            viewset=self,
            model=self.model,
            permission_policy=self.permission_policy,
            workflow_history_url_name=self.get_url_name("workflow_history"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
        )

    @property
    def workflow_preview_view(self):
        return self.workflow_preview_view_class.as_view(
            viewset=self,
            model=self.model,
        )

    @property
    def workflow_history_view(self):
        return self.workflow_history_view_class.as_view(
            viewset=self,
            model=self.model,
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            workflow_history_url_name=self.get_url_name("workflow_history"),
            workflow_history_detail_url_name=self.get_url_name(
                "workflow_history_detail"
            ),
        )

    @property
    def workflow_history_detail_view(self):
        return self.workflow_history_detail_view_class.as_view(
            viewset=self,
            model=self.model,
            object_icon=self.icon,
            permission_policy=self.permission_policy,
            workflow_history_url_name=self.get_url_name("workflow_history"),
        )

    @property
    def redirect_to_edit_view(self):
        def redirect_to_edit(request, pk):
            return redirect(self.get_url_name("edit"), pk, permanent=True)

        return redirect_to_edit

    @property
    def redirect_to_delete_view(self):
        def redirect_to_delete(request, pk):
            return redirect(self.get_url_name("delete"), pk, permanent=True)

        return redirect_to_delete

    @property
    def redirect_to_usage_view(self):
        def redirect_to_usage(request, pk):
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

    def get_templates(self, action="index", fallback=""):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        templates = [
            f"wagtailsnippets/snippets/{self.app_label}/{self.model_name}/{action}.html",
            f"wagtailsnippets/snippets/{self.app_label}/{action}.html",
            f"wagtailsnippets/snippets/{action}.html",
        ]
        if fallback:
            templates.append(fallback)
        return templates

    def get_index_template(self):
        """
        Returns a template to be used when rendering ``index_view``. If a
        template is specified by the ``index_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.index_template_name or self.get_templates("index")

    def get_index_results_template(self):
        """
        Returns a template to be used when rendering ``index_results_view``. If a
        template is specified by the ``index_results_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.index_results_template_name or self.get_templates("index_results")

    def get_create_template(self):
        """
        Returns a template to be used when rendering ``create_view``. If a
        template is specified by the ``create_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.create_template_name or self.get_templates("create")

    def get_edit_template(self):
        """
        Returns a template to be used when rendering ``edit_view``. If a
        template is specified by the ``edit_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.edit_template_name or self.get_templates("edit")

    def get_delete_template(self):
        """
        Returns a template to be used when rendering ``delete_view``. If a
        template is specified by the ``delete_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.delete_template_name or self.get_templates("delete")

    def get_history_template(self):
        """
        Returns a template to be used when rendering ``history_view``. If a
        template is specified by the ``history_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.history_template_name or self.get_templates("history")

    def get_admin_url_namespace(self):
        """Returns the URL namespace for the admin URLs for this model."""
        if self.admin_url_namespace:
            return self.admin_url_namespace
        return f"wagtailsnippets_{self.app_label}_{self.model_name}"

    def get_admin_base_path(self):
        """
        Returns the base path for the admin URLs for this model.
        The returned string must not begin or end with a slash.
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
        urlpatterns = super().get_urlpatterns() + [
            path("", self.index_view, name="list"),
            path("results/", self.index_results_view, name="list_results"),
            path("add/", self.add_view, name="add"),
            path("edit/<str:pk>/", self.edit_view, name="edit"),
            path("delete/<str:pk>/", self.delete_view, name="delete"),
            path("usage/<str:pk>/", self.usage_view, name="usage"),
            path("history/<str:pk>/", self.history_view, name="history"),
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
                    "workflow/status/<str:pk>/",
                    self.workflow_status_view,
                    name="workflow_status",
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

        legacy_redirects = [
            # legacy URLs that could potentially collide if the pk matches one of the reserved names above
            # ('add', 'edit' etc) - redirect to the unambiguous version
            path("<str:pk>/", self.redirect_to_edit_view),
            path("<str:pk>/delete/", self.redirect_to_delete_view),
            path("<str:pk>/usage/", self.redirect_to_usage_view),
        ]

        return urlpatterns + legacy_redirects

    def register_admin_url_finder(self):
        register_admin_url_finder(self.model, self.url_finder_class)

    def register_model_check(self):
        def snippets_model_check(app_configs, **kwargs):
            return check_panels_in_model(self.model, "snippets")

        checks.register(snippets_model_check, "panels")

    def register_model_methods(self):
        @classmethod
        def get_admin_url_namespace(cls):
            return self.get_admin_url_namespace()

        @classmethod
        def get_admin_base_path(cls):
            return self.get_admin_base_path()

        self.model.get_admin_url_namespace = get_admin_url_namespace
        self.model.get_admin_base_path = get_admin_base_path

    def on_register(self):
        super().on_register()
        viewsets.register(self.chooser_viewset)
        self.register_admin_url_finder()
        self.register_model_check()
        self.register_model_methods()
