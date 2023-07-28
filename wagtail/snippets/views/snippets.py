import django_filters
from django.apps import apps
from django.contrib.admin.utils import quote, unquote
from django.core import checks
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, re_path, reverse
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.filters import DateRangePickerWidget, WagtailFilterSet
from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
from wagtail.admin.panels.group import ObjectList
from wagtail.admin.panels.model_utils import extract_panel_definitions_from_model_class
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
from wagtail.admin.views.mixins import SpreadsheetExportMixin
from wagtail.admin.views.reports.base import ReportView
from wagtail.admin.viewsets import viewsets
from wagtail.admin.viewsets.model import ModelViewSet
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
        return reverse(type["model"].snippet_viewset.get_url_name("list"))

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


class IndexView(
    SpreadsheetExportMixin,
    generic.IndexViewOptionalFeaturesMixin,
    generic.IndexView,
):
    view_name = "list"
    index_results_url_name = None
    delete_url_name = None
    any_permission_required = ["add", "change", "delete"]
    page_kwarg = "p"
    table_class = InlineActionsTable

    def get_base_queryset(self):
        # Allow the queryset to be a callable that takes a request
        # so that it can be evaluated in the context of the request
        if callable(self.queryset):
            self.queryset = self.queryset(self.request)
        return super().get_base_queryset()

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

    def render_to_response(self, context, **response_kwargs):
        if self.is_export:
            return self.as_spreadsheet(
                context["object_list"], self.request.GET.get("export")
            )
        return super().render_to_response(context, **response_kwargs)


class CreateView(generic.CreateEditViewOptionalFeaturesMixin, generic.CreateView):
    view_name = "create"
    preview_url_name = None
    permission_required = "add"
    template_name = "wagtailsnippets/snippets/create.html"
    error_message = gettext_lazy("The snippet could not be created due to errors.")

    def run_before_hook(self):
        return self.run_hook("before_create_snippet", self.request, self.model)

    def run_after_hook(self):
        return self.run_hook("after_create_snippet", self.request, self.object)

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


class EditView(generic.CreateEditViewOptionalFeaturesMixin, generic.EditView):
    view_name = "edit"
    history_url_name = None
    preview_url_name = None
    revisions_compare_url_name = None
    usage_url_name = None
    permission_required = "change"
    template_name = "wagtailsnippets/snippets/edit.html"
    error_message = gettext_lazy("The snippet could not be saved due to errors.")

    def run_before_hook(self):
        return self.run_hook("before_edit_snippet", self.request, self.object)

    def run_after_hook(self):
        return self.run_hook("after_edit_snippet", self.request, self.object)

    def get_history_url(self):
        return reverse(self.history_url_name, args=[quote(self.object.pk)])

    def get_usage_url(self):
        return reverse(self.usage_url_name, args=[quote(self.object.pk)])

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
                "usage_url": self.get_usage_url(),
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


class DeleteView(generic.DeleteView):
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


class UsageView(generic.UsageView):
    view_name = "usage"
    template_name = "wagtailsnippets/snippets/usage.html"
    permission_required = "change"
    edit_url_name = None


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
    view_name = "history"
    index_url_name = None
    edit_url_name = None
    revisions_view_url_name = None
    revisions_revert_url_name = None
    revisions_compare_url_name = None
    revisions_unschedule_url_name = None
    any_permission_required = ["add", "change", "delete"]
    template_name = "wagtailsnippets/snippets/history.html"
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


class InspectView(generic.InspectView):
    view_name = "inspect"
    any_permission_required = ["add", "change", "delete"]


class PreviewOnCreateView(PreviewOnCreate):
    pass


class PreviewOnEditView(PreviewOnEdit):
    pass


class PreviewRevisionView(PermissionCheckedMixin, PreviewRevision):
    permission_required = "change"


class RevisionsCompareView(PermissionCheckedMixin, generic.RevisionsCompareView):
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


class WorkflowStatusView(PermissionCheckedMixin, workflow.WorkflowStatus):
    permission_required = "change"


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
    """

    #: The model class to be registered as a snippet with this viewset.
    model = None

    #: The icon to use across the admin for this snippet type.
    icon = "snippet"

    #: Register a custom menu item for this snippet type in the admin's main menu.
    add_to_admin_menu = False

    #: Register a custom menu item for this snippet type in the admin's "Settings" menu.
    #: This takes precedence if both ``add_to_admin_menu`` and ``add_to_settings_menu`` are set to ``True``.
    add_to_settings_menu = False

    #: The displayed label used for the menu item that appears in Wagtail's sidebar.
    #: If unset, the title-cased version of the model's :attr:`~django.db.models.Options.verbose_name_plural` will be used.
    menu_label = None

    #: The ``name`` argument passed to the ``MenuItem`` constructor, becoming the ``name`` attribute value for that instance.
    #: This can be useful when manipulating the menu items in a custom menu hook, e.g. :ref:`construct_main_menu`.
    #: If unset, a slugified version of the label is used.
    menu_name = None

    #: An integer determining the order of the menu item, 0 being the first place.
    #: If the viewset is registered within a :class:`SnippetViewSetGroup`,
    #: this is ignored and the menu item order is determined by the order of :attr:`~SnippetViewSetGroup.items`.
    menu_order = None

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

    #: A list or tuple, where each item is the name of a field, an attribute, or a single-argument callable on the model.
    list_export = []

    #: The base file name for the exported listing, without extensions. If unset, the model's :attr:`~django.db.models.Options.db_table` will be used instead.
    export_filename = None

    #: The number of items to display per page in the index view. Defaults to 20.
    list_per_page = 20

    #: The number of items to display in the chooser view. Defaults to 10.
    chooser_per_page = 10

    #: The default ordering to use for the index view. Can be a string or a list/tuple in the same format as Django's :attr:`~django.db.models.Options.ordering`.
    ordering = None

    #: The fields to use for the search in the index view.
    #: If set to ``None`` and :attr:`search_backend_name` is set to use a Wagtail search backend,
    #: the ``search_fields`` attribute of the model will be used instead.
    search_fields = None

    #: The name of the Wagtail search backend to use for the search in the index view.
    #: If set to a falsy value, the search will fall back to use Django's QuerySet API.
    search_backend_name = "default"

    #: Whether to enable the inspect view. Defaults to ``False``.
    inspect_view_enabled = False

    #: The model fields or attributes to display in the inspect view.
    #:
    #: If the field has a corresponding :meth:`~django.db.models.Model.get_FOO_display`
    #: method on the model, the method's return value will be used instead.
    #:
    #: If you have ``wagtail.images`` installed, and the field's value is an instance of
    #: ``wagtail.images.models.AbstractImage``, a thumbnail of that image will be rendered.
    #:
    #: If you have ``wagtail.documents`` installed, and the field's value is an instance of
    #: ``wagtail.docs.models.AbstractDocument``, a link to that document will be rendered,
    #: along with the document title, file extension and size.
    inspect_view_fields = []

    #: The fields to exclude from the inspect view.
    inspect_view_fields_exclude = []

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

    #: The view class to use for the inspect view; must be a subclass of ``wagtail.snippet.views.snippets.InspectView``.
    inspect_view_class = InspectView

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

    #: The prefix of template names to look for when rendering the admin views.
    template_prefix = "wagtailsnippets/snippets/"

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

    #: The template to use for the inspect view.
    inspect_template_name = ""

    def __init__(self, model=None, **kwargs):
        # Allow model to be defined on the class, or passed in via the constructor
        self.model = model or self.model

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

        self.menu_item_is_registered = (
            self.add_to_admin_menu or self.add_to_settings_menu
        )

        super().__init__(
            name=self.get_admin_url_namespace(),
            url_prefix=self.get_admin_base_path(),
            **kwargs,
        )

        if not self.list_display:
            self.list_display = self.index_view_class.list_display.copy()
            if self.draftstate_enabled:
                self.list_display += [LiveStatusTagColumn()]

        # This edit handler has been bound to the model and is used for the views.
        self._edit_handler = self.get_edit_handler()

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
            model=self.model,
            queryset=self.get_queryset,
            template_name=self.get_index_template(),
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
            list_export=self.list_export,
            export_filename=self.get_export_filename(),
            paginate_by=self.list_per_page,
            default_ordering=self.ordering,
            search_fields=self.search_fields,
            search_backend_name=self.search_backend_name,
        )

    @property
    def index_results_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            queryset=self.get_queryset,
            template_name=self.get_index_results_template(),
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
            list_export=self.list_export,
            export_filename=self.get_export_filename(),
            paginate_by=self.list_per_page,
            default_ordering=self.ordering,
            search_fields=self.search_fields,
            search_backend_name=self.search_backend_name,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            model=self.model,
            template_name=self.get_create_template(),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            panel=self._edit_handler,
            form_class=self.get_form_class(),
            index_url_name=self.get_url_name("list"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            preview_url_name=self.get_url_name("preview_on_add"),
        )

    @property
    def edit_view(self):
        # Any parameters passed here must also be passed in revisions_revert_view.
        return self.edit_view_class.as_view(
            model=self.model,
            template_name=self.get_edit_template(),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            panel=self._edit_handler,
            form_class=self.get_form_class(for_update=True),
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
            lock_url_name=self.get_url_name("lock"),
            unlock_url_name=self.get_url_name("unlock"),
            usage_url_name=self.get_url_name("usage"),
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
            model=self.model,
            template_name=self.get_delete_template(),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            delete_url_name=self.get_url_name("delete"),
            usage_url_name=self.get_url_name("usage"),
        )

    @property
    def usage_view(self):
        return self.usage_view_class.as_view(
            model=self.model,
            template_name=self.get_templates(
                "usage", fallback=self.usage_view_class.template_name
            ),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
        )

    @property
    def history_view(self):
        return self.history_view_class.as_view(
            model=self.model,
            template_name=self.get_history_template(),
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            revisions_view_url_name=self.get_url_name("revisions_view"),
            revisions_revert_url_name=self.get_url_name("revisions_revert"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
        )

    @property
    def inspect_view(self):
        return self.inspect_view_class.as_view(
            model=self.model,
            template_name=self.get_inspect_template(),
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            fields=self.inspect_view_fields,
            fields_exclude=self.inspect_view_fields_exclude,
        )

    @property
    def revisions_view(self):
        return self.revisions_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
        )

    @property
    def revisions_revert_view(self):
        return self.revisions_revert_view_class.as_view(
            model=self.model,
            template_name=self.get_edit_template(),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            panel=self._edit_handler,
            form_class=self.get_form_class(for_update=True),
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
            lock_url_name=self.get_url_name("lock"),
            unlock_url_name=self.get_url_name("unlock"),
            usage_url_name=self.get_url_name("usage"),
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
            model=self.model,
            edit_handler=self._edit_handler,
            template_name=self.get_templates(
                "revisions_compare",
                fallback=self.revisions_compare_view_class.template_name,
            ),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
        )

    @property
    def revisions_unschedule_view(self):
        return self.revisions_unschedule_view_class.as_view(
            model=self.model,
            template_name=self.get_templates(
                "revisions_unschedule",
                fallback=self.revisions_unschedule_view_class.template_name,
            ),
            header_icon=self.icon,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
        )

    @property
    def unpublish_view(self):
        return self.unpublish_view_class.as_view(
            model=self.model,
            template_name=self.get_templates(
                "unpublish", fallback=self.unpublish_view_class.template_name
            ),
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
            model=self.model,
            form_class=self.get_form_class(),
        )

    @property
    def preview_on_edit_view(self):
        return self.preview_on_edit_view_class.as_view(
            model=self.model,
            form_class=self.get_form_class(for_update=True),
        )

    @property
    def lock_view(self):
        return self.lock_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def unlock_view(self):
        return self.unlock_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            success_url_name=self.get_url_name("edit"),
        )

    @property
    def workflow_action_view(self):
        return self.workflow_action_view_class.as_view(
            model=self.model,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("workflow_action"),
        )

    @property
    def collect_workflow_action_data_view(self):
        return self.collect_workflow_action_data_view_class.as_view(
            model=self.model,
            redirect_url_name=self.get_url_name("edit"),
            submit_url_name=self.get_url_name("collect_workflow_action_data"),
        )

    @property
    def confirm_workflow_cancellation_view(self):
        return self.confirm_workflow_cancellation_view_class.as_view(model=self.model)

    @property
    def workflow_status_view(self):
        return self.workflow_status_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            workflow_history_url_name=self.get_url_name("workflow_history"),
            revisions_compare_url_name=self.get_url_name("revisions_compare"),
        )

    @property
    def workflow_preview_view(self):
        return self.workflow_preview_view_class.as_view(model=self.model)

    @property
    def workflow_history_view(self):
        return self.workflow_history_view_class.as_view(
            model=self.model,
            template_name=self.get_templates(
                "workflow_history/index",
                fallback=self.workflow_history_view_class.template_name,
            ),
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
            model=self.model,
            template_name=self.get_templates(
                "workflow_history/detail",
                fallback=self.workflow_history_detail_view_class.template_name,
            ),
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

    def get_icon(self):
        """Returns the icon to be used for the admin views."""
        return self.icon

    def get_menu_label(self):
        """Returns the label text to be used for the menu item."""
        return self.menu_label or self.model_opts.verbose_name_plural.title()

    def get_menu_name(self):
        """Returns the name to be used for the menu item."""
        return self.menu_name

    def get_menu_icon(self):
        """Returns the icon to be used for the menu item."""
        return self.get_icon()

    def get_menu_order(self):
        """Returns the ordering number to be applied to the menu item."""
        # By default, put it at the last item before Reports, whose order is 9000.
        return self.menu_order or 8999

    @property
    def menu_item_class(self):
        def is_shown(_self, request):
            return self.permission_policy.user_has_any_permission(
                request.user, ("add", "change", "delete")
            )

        return type(
            f"{self.model.__name__}MenuItem",
            (MenuItem,),
            {"is_shown": is_shown},
        )

    def get_menu_item(self, order=None):
        """
        Returns a ``MenuItem`` instance to be registered with the Wagtail admin.

        The ``order`` parameter allows the method to be called from the outside (e.g.
        :class:`SnippetViewSetGroup`) to create a sub menu item with the correct order.
        """
        return self.menu_item_class(
            label=self.get_menu_label(),
            url=reverse(self.get_url_name("index")),
            name=self.get_menu_name(),
            icon_name=self.get_menu_icon(),
            order=order or self.get_menu_order(),
        )

    def get_menu_item_is_registered(self):
        return self.menu_item_is_registered

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances to be shown on the index view.
        If ``None`` is returned (the default), the logic in
        ``index_view.get_base_queryset()`` will be used instead.
        """
        return None

    def get_export_filename(self):
        return self.export_filename or self.model_opts.db_table

    def get_templates(self, action="index", fallback=""):
        """
        Utility function that provides a list of templates to try for a given
        view, when the template isn't overridden by one of the template
        attributes on the class.
        """
        templates = [
            f"{self.template_prefix}{self.app_label}/{self.model_name}/{action}.html",
            f"{self.template_prefix}{self.app_label}/{action}.html",
            f"{self.template_prefix}{action}.html",
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

    def get_inspect_template(self):
        """
        Returns a template to be used when rendering ``inspect_view``. If a
        template is specified by the ``inspect_template_name`` attribute, that will
        be used. Otherwise, a list of preferred template names are returned.
        """
        return self.inspect_template_name or self.get_templates(
            "inspect", fallback=self.inspect_view_class.template_name
        )

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

    def get_edit_handler(self):
        """
        Returns the appropriate edit handler for this ``SnippetViewSet`` class.
        It can be defined either on the model itself or on the ``SnippetViewSet``,
        as the ``edit_handler`` or ``panels`` properties. Falls back to
        extracting panel / edit handler definitions from the model class.
        """
        if hasattr(self, "edit_handler"):
            edit_handler = self.edit_handler
        elif hasattr(self, "panels"):
            panels = self.panels
            edit_handler = ObjectList(panels)
        elif hasattr(self.model, "edit_handler"):
            edit_handler = self.model.edit_handler
        elif hasattr(self.model, "panels"):
            panels = self.model.panels
            edit_handler = ObjectList(panels)
        else:
            exclude = self.get_exclude_form_fields()
            panels = extract_panel_definitions_from_model_class(
                self.model, exclude=exclude
            )
            edit_handler = ObjectList(panels)
        return edit_handler.bind_to_model(self.model)

    def get_form_class(self, for_update=False):
        return self._edit_handler.get_form_class()

    def register_model_check(self):
        def snippets_model_check(app_configs, **kwargs):
            return check_panels_in_model(self.model, "snippets")

        checks.register(snippets_model_check, "panels")

    def register_menu_item(self):
        if self.add_to_settings_menu:
            hooks.register("register_settings_menu_item", self.get_menu_item)
        elif self.add_to_admin_menu:
            hooks.register("register_admin_menu_item", self.get_menu_item)

    def on_register(self):
        super().on_register()
        # For convenience, attach viewset to the model class to allow accessing
        # the configuration of a given model.
        self.model.snippet_viewset = self
        viewsets.register(self.chooser_viewset)
        self.register_model_check()
        self.register_menu_item()


class SnippetViewSetGroup:
    """
    A container for grouping together multiple SnippetViewSet instances. Creates
    a menu item with a submenu for accessing the listing pages of those instances.
    """

    #: A list or tuple of :class:`SnippetViewSet` classes to be grouped together
    items = ()

    #: Register a custom menu item for the group in the admin's main menu.
    add_to_admin_menu = True

    # Undocumented for now, but it is technically possible to register the group's
    # menu item in the Settings menu instead of the main menu.
    add_to_settings_menu = False

    #: The icon used for the menu item that appears in Wagtail's sidebar.
    menu_icon = None

    #: The displayed label used for the menu item.
    #: If unset, the title-cased version of the first model's :attr:`~django.db.models.Options.app_label` will be used.
    menu_label = None

    #: The ``name`` argument passed to the ``MenuItem`` constructor, becoming the ``name`` attribute value for that instance.
    #: This can be useful when manipulating the menu items in a custom menu hook, e.g. :ref:`construct_main_menu`.
    #: If unset, a slugified version of the label is used.
    menu_name = None

    #: An integer determining the order of the menu item, 0 being the first place.
    menu_order = None

    def __init__(self):
        """
        When initialising, instantiate the classes within 'items', and assign
        the instances to a ``viewsets`` attribute.
        """
        self.viewsets = [
            viewset_class(menu_item_is_registered=True) for viewset_class in self.items
        ]

    def get_app_label_from_subitems(self):
        for instance in self.viewsets:
            return instance.app_label.title()
        return ""

    def get_menu_label(self):
        """Returns the label text to be used for the menu item."""
        return self.menu_label or self.get_app_label_from_subitems()

    def get_menu_name(self):
        """Returns the name to be used for the menu item."""
        return self.menu_name

    def get_menu_icon(self):
        """Returns the icon to be used for the menu item."""
        return self.menu_icon or "folder-open-inverse"

    def get_menu_order(self):
        """Returns the ordering number to be applied to the menu item."""
        return self.menu_order or 8999

    def get_submenu_items(self):
        menu_items = []
        item_order = 1
        for viewset in self.viewsets:
            menu_items.append(viewset.get_menu_item(order=item_order))
            item_order += 1
        return menu_items

    def get_menu_item(self):
        """Returns a ``MenuItem`` instance to be registered with the Wagtail admin."""
        if not self.viewsets:
            return None
        submenu = Menu(items=self.get_submenu_items())
        return SubmenuMenuItem(
            label=self.get_menu_label(),
            menu=submenu,
            name=self.get_menu_name(),
            icon_name=self.get_menu_icon(),
            order=self.get_menu_order(),
        )

    def register_menu_item(self):
        if self.add_to_settings_menu:
            hooks.register("register_settings_menu_item", self.get_menu_item)
        elif self.add_to_admin_menu:
            hooks.register("register_admin_menu_item", self.get_menu_item)

    def on_register(self):
        self.register_menu_item()
