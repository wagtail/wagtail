from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.http import Http404
from django.urls import path
from django.utils.functional import cached_property, classproperty

from wagtail.admin.views.page_privacy import set_privacy
from wagtail.admin.views.pages.choose_parent import (
    ChooseParentView,
    GenericChooseParentView,
)
from wagtail.admin.views.pages.convert_alias import convert_alias
from wagtail.admin.views.pages.copy import copy
from wagtail.admin.views.pages.create import CreateView, add_subpage
from wagtail.admin.views.pages.delete import delete
from wagtail.admin.views.pages.edit import EditView
from wagtail.admin.views.pages.history import (
    PageHistoryView,
    WorkflowHistoryDetailView,
    WorkflowHistoryView,
)
from wagtail.admin.views.pages.listing import (
    ExplorableIndexView,
    GenericPageFilterSet,
    IndexView,
    PageFilterSet,
)
from wagtail.admin.views.pages.lock import LockView, UnlockView
from wagtail.admin.views.pages.move import MoveChooseDestination, move_confirm
from wagtail.admin.views.pages.ordering import set_page_position
from wagtail.admin.views.pages.preview import PreviewOnCreate, PreviewOnEdit, view_draft
from wagtail.admin.views.pages.revisions import (
    RevisionsCompare,
    RevisionsRevertView,
    RevisionsUnschedule,
    RevisionsView,
)
from wagtail.admin.views.pages.unpublish import Unpublish
from wagtail.admin.views.pages.usage import ContentTypeUseView, UsageView
from wagtail.admin.views.pages.workflow import (
    CollectWorkflowActionData,
    ConfirmWorkflowCancellation,
    PreviewRevisionForTask,
    WorkflowAction,
)
from wagtail.admin.viewsets.listing import ListingViewSetMixin
from wagtail.models import Page
from wagtail.utils.registry import ObjectTypeRegistry

from .base import ViewSet


class PageListingViewSet(ListingViewSetMixin, ViewSet):
    """
    A viewset to present a flat listing of all pages of a specific type.
    All attributes and methods from :class:`~wagtail.admin.viewsets.base.ViewSet`
    are available.
    For more information on how to use this class, see :ref:`custom_flat_page_listings`.
    """

    #: The view class to use for the index view; must be a subclass of ``wagtail.admin.views.pages.listing.IndexView``.
    index_view_class = IndexView
    #: The view class to use for choosing the parent page when creating a new page of this page type.
    choose_parent_view_class = ChooseParentView
    #: Required; the page model class that this viewset will work with.
    model = Page

    columns = classproperty()
    """
    A list of :class:`~wagtail.admin.ui.tables.Column` instances for the columns in the listing.
    This takes priority over :attr:`list_display` if both are defined.
    """

    @columns.getter
    def columns(cls):
        # For backwards compatibility, use a classproperty so existing code that
        # directly extends the viewset's columns attribute will continue to
        # work, while allowing new code to set columns to automatically generate
        # the columns for the listing with list_display.
        if cls.list_display is cls.UNDEFINED:
            return cls.index_view_class.base_columns
        return cls.UNDEFINED

    @classproperty
    def filterset_class(cls):
        # For backwards compatibility, use a classproperty so existing code that
        # directly subclasses the viewset's filterset_class attribute will
        # continue to work, while allowing new code to use list_filter to
        # automatically generate a filterset class if desired.
        if not cls.list_filter or cls.list_filter is cls.UNDEFINED:
            if cls.model is Page:
                # Add filter by content type
                return GenericPageFilterSet
            return PageFilterSet
        # The filterset class generation is done in IndexView with a
        # cached_property, so we need to use UNDEFINED here to avoid overwriting
        # that logic.
        return cls.UNDEFINED

    @cached_property
    def export_filename(self):
        """
        The base file name for the exported listing, without extensions.
        If unset, the model's :attr:`~django.db.models.Options.db_table` will be
        used instead.
        """
        return self.model._meta.db_table

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "header_icon": self.icon,
                "model": self.model,
                "index_url_name": self.get_url_name("index"),
                "add_url_name": self.get_url_name("choose_parent"),
                **kwargs,
            }
        )

    def get_index_view_kwargs(self, **kwargs):
        return super().get_index_view_kwargs(
            **{
                "index_results_url_name": self.get_url_name("index_results"),
                "columns": self.columns,
                **kwargs,
            }
        )

    def get_choose_parent_view_kwargs(self, **kwargs):
        return kwargs

    @cached_property
    def index_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs()
        )

    @cached_property
    def index_results_view(self):
        return self.construct_view(
            self.index_view_class, **self.get_index_view_kwargs(), results_only=True
        )

    @cached_property
    def choose_parent_view(self):
        return self.construct_view(
            self.choose_parent_view_class, **self.get_choose_parent_view_kwargs()
        )

    def get_urlpatterns(self):
        return [
            path("", self.index_view, name="index"),
            path("results/", self.index_results_view, name="index_results"),
            path("choose_parent/", self.choose_parent_view, name="choose_parent"),
        ]


class PageViewSet(PageListingViewSet):
    """
    A viewset to define the views for pages of a specific type.
    For more information on how to use this class, see :ref:`custom_default_page_listings`.
    """

    choose_parent_view_class = GenericChooseParentView
    """
    The view class to use for choosing the parent page when creating a new page of this page type;
    must be a subclass of ``wagtail.admin.views.pages.choose_parent.GenericChooseParentView``.
    """
    content_type_use_view_class = ContentTypeUseView
    """
    The view class to use for the flat per-page-type index view; must be a subclass of
    ``wagtail.admin.views.pages.usage.ContentTypeUseView``.
    """
    add_view_class = CreateView
    """
    The view class to use for the create view; must be a subclass of
    ``wagtail.admin.views.pages.create.CreateView``.
    """
    collect_workflow_action_data_view_class = CollectWorkflowActionData
    """
    The view class to use for the workflow action data collection view; must be a subclass of
    ``wagtail.admin.views.pages.workflow.CollectWorkflowActionData``.
    """
    confirm_workflow_cancellation_view_class = ConfirmWorkflowCancellation
    """
    The view class to use for the workflow cancellation confirmation view; must be a subclass of
    ``wagtail.admin.views.pages.workflow.ConfirmWorkflowCancellation``.
    """
    edit_view_class = EditView
    """
    The view class to use for the edit view; must be a subclass of
    ``wagtail.admin.views.pages.edit.EditView``.
    """
    history_view_class = PageHistoryView
    """
    The view class to use for the history view; must be a subclass of
    ``wagtail.admin.views.pages.history.PageHistoryView``.
    """
    index_view_class = ExplorableIndexView
    """
    The view class to use for the index view; must be a subclass of
    ``wagtail.admin.views.pages.listing.ExplorableIndexView``.
    """
    lock_view_class = LockView
    """
    The view class to use for the lock view; must be a subclass of
    ``wagtail.admin.views.pages.lock.LockView``.
    """
    move_view_class = MoveChooseDestination
    """
    The view class to use for the move choose destination view; must be a subclass of
    ``wagtail.admin.views.pages.move.MoveChooseDestination``.
    """
    unlock_view_class = UnlockView
    """
    The view class to use for the unlock view; must be a subclass of
    ``wagtail.admin.views.pages.lock.UnlockView``.
    """
    preview_on_add_view_class = PreviewOnCreate
    """
    The view class to use for the preview on create view; must be a subclass of
    ``wagtail.admin.views.pages.preview.PreviewOnCreate``.
    """
    preview_on_edit_view_class = PreviewOnEdit
    """
    The view class to use for the preview on edit view; must be a subclass of
    ``wagtail.admin.views.pages.preview.PreviewOnEdit``.
    """
    revisions_view_class = RevisionsView
    """
    The view class to use for the revisions view; must be a subclass of
    ``wagtail.admin.views.pages.revisions.RevisionsView``.
    """
    revisions_compare_view_class = RevisionsCompare
    """
    The view class to use for the revisions compare view; must be a subclass of
    ``wagtail.admin.views.pages.revisions.RevisionsCompare``.
    """
    revisions_revert_view_class = RevisionsRevertView
    """
    The view class to use for the revisions revert view; must be a subclass of
    ``wagtail.admin.views.pages.revisions.RevisionsRevertView``.
    """
    revisions_unschedule_view_class = RevisionsUnschedule
    """
    The view class to use for the revisions unschedule view; must be a subclass of
    ``wagtail.admin.views.pages.revisions.RevisionsUnschedule``.
    """
    unpublish_view_class = Unpublish
    """
    The view class to use for the unpublish view; must be a subclass of
    ``wagtail.admin.views.pages.unpublish.Unpublish``.
    """
    usage_view_class = UsageView
    """
    The view class to use for the usage view; must be a subclass of
    ``wagtail.admin.views.pages.usage.UsageView``.
    """
    workflow_action_view_class = WorkflowAction
    """
    The view class to use for the workflow action view; must be a subclass of
    ``wagtail.admin.views.pages.workflow.WorkflowAction``.
    """
    workflow_history_view_class = WorkflowHistoryView
    """
    The view class to use for the workflow history view; must be a subclass of
    ``wagtail.admin.views.pages.history.WorkflowHistoryView``.
    """
    workflow_history_detail_view_class = WorkflowHistoryDetailView
    """
    The view class to use for the workflow history detail view; must be a subclass of
    ``wagtail.admin.views.pages.history.WorkflowHistoryDetailView``.
    """
    workflow_preview_view_class = PreviewRevisionForTask
    """
    The view class to use for the workflow preview revision for task view; must be a subclass of
    ``wagtail.admin.views.pages.workflow.PreviewRevisionForTask``.
    """
    menu_url = None
    """Unused. There is no specific URL to link to for the menu item."""

    @cached_property
    def views(self):
        return {
            "add": self.add_view,
            "add_subpage": self.add_subpage_view,
            "choose_parent": self.choose_parent_view,
            "collect_workflow_action_data": self.collect_workflow_action_data_view,
            "confirm_workflow_cancellation": self.confirm_workflow_cancellation_view,
            "content_type_use": self.content_type_use_view,
            "content_type_use_results": self.content_type_use_results_view,
            "convert_alias": self.convert_alias_view,
            "copy": self.copy_view,
            "delete": self.delete_view,
            "edit": self.edit_view,
            "history": self.history_view,
            "history_results": self.history_results_view,
            "index": self.index_view,
            "index_results": self.index_results_view,
            "lock": self.lock_view,
            "move": self.move_view,
            "move_confirm": self.move_confirm_view,
            "preview_on_add": self.preview_on_add_view,
            "preview_on_edit": self.preview_on_edit_view,
            "revisions_compare": self.revisions_compare_view,
            "revisions_view": self.revisions_view,
            "revisions_unschedule": self.revisions_unschedule_view,
            "revisions_revert": self.revisions_revert_view,
            "set_page_position": self.set_page_position_view,
            "set_privacy": self.set_privacy_view,
            "unlock": self.unlock_view,
            "unpublish": self.unpublish_view,
            "usage": self.usage_view,
            "view_draft": self.view_draft_view,
            "workflow_action": self.workflow_action_view,
            "workflow_history": self.workflow_history_view,
            "workflow_history_detail": self.workflow_history_detail_view,
            "workflow_preview": self.workflow_preview_view,
        }

    def get_view_by_name(self, name):
        return self.views[name]

    @cached_property
    def content_type_use_view(self):
        return self.construct_view(
            self.content_type_use_view_class,
            **self.get_index_view_kwargs(),
        )

    @cached_property
    def content_type_use_results_view(self):
        return self.construct_view(
            self.content_type_use_view_class,
            **self.get_index_view_kwargs(),
            results_only=True,
        )

    @cached_property
    def add_view(self):
        return self.construct_view(self.add_view_class)

    add_subpage_view = staticmethod(add_subpage)

    @cached_property
    def collect_workflow_action_data_view(self):
        return self.construct_view(self.collect_workflow_action_data_view_class)

    @cached_property
    def confirm_workflow_cancellation_view(self):
        return self.construct_view(self.confirm_workflow_cancellation_view_class)

    convert_alias_view = staticmethod(convert_alias)

    copy_view = staticmethod(copy)

    delete_view = staticmethod(delete)

    @cached_property
    def edit_view(self):
        return self.construct_view(self.edit_view_class)

    @cached_property
    def history_view(self):
        return self.construct_view(self.history_view_class)

    @cached_property
    def history_results_view(self):
        return self.construct_view(
            self.history_view_class,
            results_only=True,
        )

    @cached_property
    def lock_view(self):
        return self.construct_view(self.lock_view_class)

    @cached_property
    def move_view(self):
        return self.construct_view(self.move_view_class)

    move_confirm_view = staticmethod(move_confirm)

    @cached_property
    def preview_on_add_view(self):
        return self.construct_view(self.preview_on_add_view_class)

    @cached_property
    def preview_on_edit_view(self):
        return self.construct_view(self.preview_on_edit_view_class)

    @cached_property
    def revisions_view(self):
        return self.construct_view(self.revisions_view_class)

    @cached_property
    def revisions_compare_view(self):
        return self.construct_view(self.revisions_compare_view_class)

    @cached_property
    def revisions_revert_view(self):
        return self.construct_view(self.revisions_revert_view_class)

    @cached_property
    def revisions_unschedule_view(self):
        return self.construct_view(self.revisions_unschedule_view_class)

    set_page_position_view = staticmethod(set_page_position)

    set_privacy_view = staticmethod(set_privacy)

    @cached_property
    def unlock_view(self):
        return self.construct_view(self.unlock_view_class)

    @cached_property
    def unpublish_view(self):
        return self.construct_view(self.unpublish_view_class)

    @cached_property
    def usage_view(self):
        return self.construct_view(self.usage_view_class)

    view_draft_view = staticmethod(view_draft)

    @cached_property
    def workflow_action_view(self):
        return self.construct_view(self.workflow_action_view_class)

    @cached_property
    def workflow_history_view(self):
        return self.construct_view(self.workflow_history_view_class)

    @cached_property
    def workflow_history_detail_view(self):
        return self.construct_view(self.workflow_history_detail_view_class)

    @cached_property
    def workflow_preview_view(self):
        return self.construct_view(self.workflow_preview_view_class)

    @cached_property
    def parent_models(self):
        """
        The parent page models to associate in the main page explorer, so this
        viewset's listing view will be used when exploring the parent page
        models' children. This allows displaying, filtering, and ordering on
        fields of a specific child page model in the explorer.

        By default, if the main :attr:`model`
        :attr:`~wagtail.models.Page.parent_page_types` is defined, this will be
        every model in the list that also defines
        :attr:`~wagtail.models.Page.subpage_types` with only this viewset's
        model (or its subclasses). In other words, this will apply to this
        viewset model's parents that only allow this viewset model (or its
        subclasses) as children.

        Otherwise, the viewset's listing view customizations will not have any
        effect.
        """
        if self.model is Page:
            return [Page]
        return [
            model
            for model in self.model.allowed_parent_page_models()
            if all(
                issubclass(child_model, self.model)
                for child_model in model.allowed_subpage_models()
            )
        ]

    def get_url_name(self, view_name):
        """
        Unused. URL names are shared across all page types and are defined
        in the view classes directly.
        """
        return self.UNDEFINED

    def get_urlpatterns(self):
        """
        Unused. URL patterns are shared across all page types and defined in
        the main URL configuration. A thin view wrapper is used to route to the
        appropriate viewset based on the model of the page being accessed.
        """
        return []

    def on_register(self):
        """Register the viewset to the global page viewset registry."""
        super().on_register()
        page_viewset_registry.register(
            self.model, self, parent_models=self.parent_models
        )


class PageViewSetRegistry(ObjectTypeRegistry):
    def __init__(self):
        super().__init__()
        self.values_by_parent_model = {}

    def get_content_type_id_by_page_id(self, page_id):
        return (
            Page.objects.filter(pk=page_id)
            .values_list("content_type_id", flat=True)
            .get()
        )

    def get_page_model_by_content_type_id(self, content_type_id):
        # A stale content type's model_class() returns None, fall back to base Page.
        return ContentType.objects.get_for_id(content_type_id).model_class() or Page

    def get_by_parent_model(self, cls):
        for ancestor in cls.mro():
            try:
                return self.values_by_parent_model[ancestor]
            except KeyError:
                pass

    def get_by_page_id(self, page_id):
        """Get a viewset by the page ID whose model is registered."""
        # Only fetch the content type ID to optimise the query, as the full page
        # instance will be fetched later by the view itself.
        content_type_id = self.get_content_type_id_by_page_id(page_id)
        model = self.get_page_model_by_content_type_id(content_type_id)
        return self.get_by_type(model)

    def get_by_parent_page_id(self, parent_page_id):
        """Get a viewset by the parent page ID whose model is registered."""
        # Only fetch the content type ID to optimise the query, as the full page
        # instance will be fetched later by the view itself.
        content_type_id = self.get_content_type_id_by_page_id(parent_page_id)
        model = self.get_page_model_by_content_type_id(content_type_id)
        return self.get_by_parent_model(model)

    def get_by_content_type_natural_key(self, app_label, model_name):
        content_type = ContentType.objects.get_by_natural_key(app_label, model_name)
        model = content_type.model_class() or Page
        if not issubclass(model, Page):
            raise Http404
        return self.get_by_type(model)

    def register(self, cls, value=None, exact_class=False, parent_models=()):
        super().register(cls, value, exact_class)
        for parent_model in parent_models:
            self.values_by_parent_model[parent_model] = value

    def as_view(
        self,
        view_name,
        page_id_kwarg=None,
        parent_page_id_kwarg=None,
        app_label_kwarg=None,
        model_name_kwarg=None,
    ):
        """
        Create a view function that routes to the appropriate view based on the
        model of the page being accessed.

        This allows the use of custom views for specific page types, while still
        using the same URL pattern for all page types.
        """

        if page_id_kwarg:

            def get_viewset(kwargs):
                return self.get_by_page_id(kwargs.get(page_id_kwarg))

        elif parent_page_id_kwarg:

            def get_viewset(kwargs):
                return self.get_by_parent_page_id(kwargs.get(parent_page_id_kwarg))

        elif app_label_kwarg and model_name_kwarg:

            def get_viewset(kwargs):
                return self.get_by_content_type_natural_key(
                    kwargs.get(app_label_kwarg),
                    kwargs.get(model_name_kwarg),
                )

        else:
            raise ImproperlyConfigured(
                f"PageViewSetRegistry.as_view('{view_name}', …) requires one "
                "of the following combinations of kwargs:\n"
                "- page_id_kwarg,\n"
                "- parent_page_id_kwarg, or\n"
                "- app_label_kwarg and model_name_kwarg."
            )

        def view_router(request, *args, **kwargs):
            try:
                viewset = get_viewset(kwargs)
                view = viewset.get_view_by_name(view_name)
            except (ObjectDoesNotExist, KeyError) as e:
                # Page, ContentType, or view name not found
                raise Http404 from e
            return view(request, *args, **kwargs)

        return view_router


page_viewset_registry = PageViewSetRegistry()

# Provide a fallback default viewset for any page types that don't have a custom
# viewset, to be registered via the register_admin_viewset hook.
base_page_viewset = PageViewSet()
