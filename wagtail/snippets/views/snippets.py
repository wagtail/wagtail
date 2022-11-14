import warnings
from functools import partial
from urllib.parse import urlencode

import django_filters
from django.apps import apps
from django.contrib.admin.utils import quote, unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, re_path, reverse
from django.utils import timezone
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext

from wagtail.admin import messages
from wagtail.admin.admin_url_finder import AdminURLFinder, register_admin_url_finder
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
from wagtail.admin.views.generic.mixins import RevisionsRevertMixin
from wagtail.admin.views.generic.permissions import PermissionCheckedMixin
from wagtail.admin.views.generic.preview import PreviewOnCreate as PreviewOnCreateView
from wagtail.admin.views.generic.preview import PreviewOnEdit as PreviewOnEditView
from wagtail.admin.views.generic.preview import PreviewRevision
from wagtail.admin.views.reports.base import ReportView
from wagtail.admin.viewsets.base import ViewSet
from wagtail.log_actions import log
from wagtail.log_actions import registry as log_registry
from wagtail.models import DraftStateMixin, Locale, PreviewableMixin, RevisionMixin
from wagtail.models.audit_log import ModelLogEntry
from wagtail.permissions import ModelPermissionPolicy
from wagtail.snippets.action_menu import SnippetActionMenu
from wagtail.snippets.models import SnippetAdminURLFinder, get_snippet_models
from wagtail.snippets.permissions import user_can_edit_snippet_type
from wagtail.snippets.side_panels import SnippetSidePanels
from wagtail.utils.deprecation import RemovedInWagtail50Warning


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


def get_snippet_edit_handler(model):
    warnings.warn(
        "The get_snippet_edit_handler function has been moved to wagtail.admin.panels.get_edit_handler",
        category=RemovedInWagtail50Warning,
        stacklevel=2,
    )
    return get_edit_handler(model)


# == Views ==


class ModelIndexView(generic.IndexView):
    template_name = "wagtailadmin/generic/index.html"
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


class SnippetTitleColumn(TitleColumn):
    cell_template_name = "wagtailsnippets/snippets/tables/title_cell.html"


class IndexView(generic.IndexView):
    view_name = "list"
    index_results_url_name = None
    delete_multiple_url_name = None
    any_permission_required = ["add", "change", "delete"]
    paginate_by = 20
    page_kwarg = "p"
    # If true, returns just the 'results' include, for use in AJAX responses from search
    results_only = False
    table_class = InlineActionsTable

    def _get_title_column(self, field_name, column_class=SnippetTitleColumn, **kwargs):
        accessor = kwargs.pop("accessor", None)

        if not accessor and field_name == "__str__":

            def accessor(obj):
                if isinstance(obj, DraftStateMixin) and obj.latest_revision:
                    return obj.latest_revision.object_str
                return str(obj)

        return super()._get_title_column(
            field_name, column_class, accessor=accessor, **kwargs
        )

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
                "can_delete_snippets": self.permission_policy.user_has_permission(
                    self.request.user, "delete"
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
            return ["wagtailsnippets/snippets/results.html"]
        else:
            return ["wagtailsnippets/snippets/type_index.html"]


class CreateView(generic.CreateView):
    view_name = "create"
    preview_url_name = None
    permission_required = "add"
    template_name = "wagtailsnippets/snippets/create.html"
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
        urlquery = ""
        if self.locale and self.object.locale is not Locale.get_default():
            urlquery = "?locale=" + self.object.locale.language_code

        return reverse(self.index_url_name) + urlquery

    def get_success_message(self, instance):
        message = _("%(snippet_type)s '%(instance)s' created.")
        if isinstance(instance, DraftStateMixin) and self.action == "publish":
            message = _("%(snippet_type)s '%(instance)s' created and published.")
            if instance.go_live_at and instance.go_live_at > timezone.now():
                message = _(
                    "%(snippet_type)s '%(instance)s' created and scheduled for publishing."
                )

        return message % {
            "snippet_type": capfirst(self.model._meta.verbose_name),
            "instance": instance,
        }

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(
                    self.edit_url_name,
                    args=[quote(self.object.pk)],
                ),
                _("Edit"),
            )
        ]

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


class EditView(generic.EditView):
    view_name = "edit"
    history_url_name = None
    preview_url_name = None
    permission_required = "change"
    template_name = "wagtailsnippets/snippets/edit.html"
    error_message = gettext_lazy("The snippet could not be saved due to errors.")

    def run_before_hook(self):
        return self.run_hook("before_edit_snippet", self.request, self.object)

    def run_after_hook(self):
        return self.run_hook("after_edit_snippet", self.request, self.object)

    def setup(self, request, *args, pk, **kwargs):
        self.pk = pk
        self.object = self.get_object()
        super().setup(request, *args, **kwargs)

    def get_panel(self):
        return get_edit_handler(self.model)

    def get_object(self, queryset=None):
        self.live_object = get_object_or_404(self.model, pk=unquote(self.pk))

        if issubclass(self.model, DraftStateMixin):
            return self.live_object.get_latest_revision_as_object()
        return self.live_object

    def get_edit_url(self):
        return reverse(
            self.edit_url_name,
            args=[quote(self.object.pk)],
        )

    def get_delete_url(self):
        # This actually isn't used because we use a custom action menu
        return reverse(
            self.delete_url_name,
            args=[quote(self.object.pk)],
        )

    def get_history_url(self):
        return reverse(
            self.history_url_name,
            args=[quote(self.object.pk)],
        )

    def get_success_url(self):
        return reverse(self.index_url_name)

    def get_success_message(self):
        message = _("%(snippet_type)s '%(instance)s' updated.")

        if self.draftstate_enabled and self.action == "publish":
            message = _("%(snippet_type)s '%(instance)s' updated and published.")

            if self.object.go_live_at and self.object.go_live_at > timezone.now():
                message = _(
                    "%(snippet_type)s '%(instance)s' has been scheduled for publishing."
                )

                if self.object.live:
                    message = _(
                        "%(snippet_type)s '%(instance)s' is live and this version has been scheduled for publishing."
                    )

        return message % {
            "snippet_type": capfirst(self.model._meta.verbose_name),
            "instance": self.object,
        }

    def get_success_buttons(self):
        return [
            messages.button(
                reverse(
                    self.edit_url_name,
                    args=[quote(self.object.pk)],
                ),
                _("Edit"),
            )
        ]

    def _get_action_menu(self):
        return SnippetActionMenu(
            self.request, view=self.view_name, instance=self.object
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
    delete_multiple_url_name = None
    permission_required = "delete"
    template_name = "wagtailsnippets/snippets/confirm_delete.html"

    def run_before_hook(self):
        return self.run_hook("before_delete_snippet", self.request, self.objects)

    def run_after_hook(self):
        return self.run_hook("after_delete_snippet", self.request, self.objects)

    def setup(self, request, *args, pk=None, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.objects = self.get_objects()

    def get_object(self, queryset=None):
        # DeleteView requires either a pk kwarg or a positional arg, but we use
        # an `id` query param for multiple objects. We need to explicitly override
        # this so that we don't have to override `post()`.
        return None

    def get_objects(self):
        # Replaces get_object to allow returning multiple objects instead of just one

        if self.pk:
            return [get_object_or_404(self.model, pk=unquote(self.pk))]

        ids = self.request.GET.getlist("id")
        objects = self.model.objects.filter(pk__in=ids)
        return objects

    def get_delete_url(self):
        return (
            reverse(
                self.delete_multiple_url_name,
            )
            + "?"
            + urlencode([("id", instance.pk) for instance in self.objects])
        )

    def get_success_message(self):
        count = len(self.objects)
        if count == 1:
            return _("%(snippet_type)s '%(instance)s' deleted.") % {
                "snippet_type": capfirst(self.model._meta.verbose_name),
                "instance": self.objects[0],
            }

        # This message is only used in plural form, but we'll define it with ngettext so that
        # languages with multiple plural forms can be handled correctly (or, at least, as
        # correctly as possible within the limitations of verbose_name_plural...)
        return ngettext(
            "%(count)d %(snippet_type)s deleted.",
            "%(count)d %(snippet_type)s deleted.",
            count,
        ) % {
            "snippet_type": capfirst(self.model._meta.verbose_name_plural),
            "count": count,
        }

    def delete_action(self):
        with transaction.atomic():
            for instance in self.objects:
                log(instance=instance, action="wagtail.delete")
                instance.delete()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "model_opts": self.model._meta,
                "objects": self.objects,
                "action_url": self.get_delete_url(),
            }
        )
        return context


class UsageView(generic.IndexView):
    view_name = "usage"
    template_name = "wagtailsnippets/snippets/usage.html"
    paginate_by = 20
    page_kwarg = "p"
    is_searchable = False
    permission_required = "change"

    def setup(self, request, *args, pk, **kwargs):
        super().setup(request, *args, **kwargs)
        self.pk = pk
        self.object = self.get_object()

    def get_object(self):
        object = get_object_or_404(self.model, pk=unquote(self.pk))
        if isinstance(object, DraftStateMixin):
            return object.get_latest_revision_as_object()
        return object

    def get_queryset(self):
        return self.object.get_usage()

    def paginate_queryset(self, queryset, page_size):
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )

        page_number = self.request.GET.get(self.page_kwarg)
        page = paginator.get_page(page_number)

        # Add edit URLs to each source object
        url_finder = AdminURLFinder(self.request.user)
        for object, references in page:
            object.edit_url = url_finder.get_edit_url(object)

        return (paginator, page, page.object_list, page.has_other_pages())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add edit URLs to each source object
        url_finder = AdminURLFinder(self.request.user)
        results = []
        for object, references in context.get("page_obj"):
            edit_url = url_finder.get_edit_url(object)
            if edit_url is None:
                label = _("(Private %s)") % object._meta.verbose_name
                edit_link_title = None
            else:
                label = str(object)
                edit_link_title = _("Edit this %s") % object._meta.verbose_name
            results.append((label, edit_url, edit_link_title, references))

        context.update(
            {
                "object": self.object,
                "results": results,
                "model_opts": self.model._meta,
            }
        )
        return context


def redirect_to_edit(request, app_label, model_name, pk):
    return redirect(
        f"wagtailsnippets_{app_label}_{model_name}:edit", pk, permanent=True
    )


def redirect_to_delete(request, app_label, model_name, pk):
    return redirect(
        f"wagtailsnippets_{app_label}_{model_name}:delete", pk, permanent=True
    )


def redirect_to_usage(request, app_label, model_name, pk):
    return redirect(
        f"wagtailsnippets_{app_label}_{model_name}:usage", pk, permanent=True
    )


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


class PreviewRevisionView(PermissionCheckedMixin, PreviewRevision):
    permission_required = "change"


class RevisionsCompareView(PermissionCheckedMixin, generic.RevisionsCompareView):
    permission_required = "change"
    header_icon = "snippet"

    @property
    def edit_label(self):
        return _("Edit this {model_name}").format(
            model_name=self.model._meta.verbose_name
        )

    @property
    def history_label(self):
        return _("{model_name} history").format(
            model_name=self.model._meta.verbose_name
        )


class UnpublishView(PermissionCheckedMixin, generic.UnpublishView):
    permission_required = "publish"


class RevisionsUnscheduleView(PermissionCheckedMixin, generic.RevisionsUnscheduleView):
    permission_required = "change"


class SnippetViewSet(ViewSet):
    """
    A viewset that instantiates the admin views for snippets.
    """

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

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.preview_enabled = issubclass(self.model, PreviewableMixin)
        self.revision_enabled = issubclass(self.model, RevisionMixin)
        self.draftstate_enabled = issubclass(self.model, DraftStateMixin)

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
            (RevisionsRevertMixin, self.edit_view_class),
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
            filterset_class=self.filterset_class,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            index_results_url_name=self.get_url_name("list_results"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            delete_multiple_url_name=self.get_url_name("delete-multiple"),
            list_display=self.list_display,
        )

    @property
    def index_results_view(self):
        return self.index_view_class.as_view(
            model=self.model,
            filterset_class=self.filterset_class,
            permission_policy=self.permission_policy,
            results_only=True,
            index_url_name=self.get_url_name("list"),
            index_results_url_name=self.get_url_name("list_results"),
            add_url_name=self.get_url_name("add"),
            edit_url_name=self.get_url_name("edit"),
            delete_multiple_url_name=self.get_url_name("delete-multiple"),
            list_display=self.list_display,
        )

    @property
    def add_view(self):
        return self.add_view_class.as_view(
            model=self.model,
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
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
        )

    @property
    def delete_view(self):
        return self.delete_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            delete_multiple_url_name=self.get_url_name("delete-multiple"),
        )

    @property
    def usage_view(self):
        return self.usage_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
        )

    @property
    def history_view(self):
        return self.history_view_class.as_view(
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
            model=self.model,
            permission_policy=self.permission_policy,
        )

    @property
    def revisions_revert_view(self):
        return self.revisions_revert_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            delete_url_name=self.get_url_name("delete"),
            history_url_name=self.get_url_name("history"),
            preview_url_name=self.get_url_name("preview_on_edit"),
            revisions_revert_url_name=self.get_url_name("revisions_revert"),
        )

    @property
    def revisions_compare_view(self):
        return self.revisions_compare_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
        )

    @property
    def revisions_unschedule_view(self):
        return self.revisions_unschedule_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            edit_url_name=self.get_url_name("edit"),
            history_url_name=self.get_url_name("history"),
            revisions_unschedule_url_name=self.get_url_name("revisions_unschedule"),
        )

    @property
    def unpublish_view(self):
        return self.unpublish_view_class.as_view(
            model=self.model,
            permission_policy=self.permission_policy,
            index_url_name=self.get_url_name("list"),
            edit_url_name=self.get_url_name("edit"),
            unpublish_url_name=self.get_url_name("unpublish"),
        )

    @property
    def preview_on_add_view(self):
        return self.preview_on_add_view_class.as_view(model=self.model)

    @property
    def preview_on_edit_view(self):
        return self.preview_on_edit_view_class.as_view(model=self.model)

    @property
    def redirect_to_edit_view(self):
        return partial(
            redirect_to_edit,
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
        )

    @property
    def redirect_to_delete_view(self):
        return partial(
            redirect_to_delete,
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
        )

    @property
    def redirect_to_usage_view(self):
        return partial(
            redirect_to_usage,
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
        )

    def get_urlpatterns(self):
        urlpatterns = super().get_urlpatterns() + [
            path("", self.index_view, name="list"),
            path("results/", self.index_results_view, name="list_results"),
            path("add/", self.add_view, name="add"),
            path("edit/<str:pk>/", self.edit_view, name="edit"),
            path("multiple/delete/", self.delete_view, name="delete-multiple"),
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

        legacy_redirects = [
            # legacy URLs that could potentially collide if the pk matches one of the reserved names above
            # ('add', 'edit' etc) - redirect to the unambiguous version
            path("<str:pk>/", self.redirect_to_edit_view),
            path("<str:pk>/delete/", self.redirect_to_delete_view),
            path("<str:pk>/usage/", self.redirect_to_usage_view),
        ]

        return urlpatterns + legacy_redirects

    def on_register(self):
        super().on_register()
        url_finder_class = type(
            "_SnippetAdminURLFinder", (SnippetAdminURLFinder,), {"model": self.model}
        )
        register_admin_url_finder(self.model, url_finder_class)
