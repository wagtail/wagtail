from django.urls import path, re_path

from wagtail.admin.views import page_privacy
from wagtail.admin.views.pages import (
    convert_alias,
    copy,
    create,
    delete,
    edit,
    history,
    lock,
    moderation,
    move,
    ordering,
    preview,
    revisions,
    search,
    unpublish,
    usage,
    workflow,
)

app_name = "wagtailadmin_pages"
urlpatterns = [
    path(
        "add/<slug:content_type_app_name>/<slug:content_type_model_name>/<int:parent_page_id>/",
        create.CreateView.as_view(),
        name="add",
    ),
    path(
        "add/<slug:content_type_app_name>/<slug:content_type_model_name>/<int:parent_page_id>/preview/",
        preview.PreviewOnCreate.as_view(),
        name="preview_on_add",
    ),
    path(
        "usage/<slug:content_type_app_name>/<slug:content_type_model_name>/",
        usage.content_type_use,
        name="type_use",
    ),
    path("<int:page_id>/edit/", edit.EditView.as_view(), name="edit"),
    path(
        "<int:page_id>/edit/preview/",
        preview.PreviewOnEdit.as_view(),
        name="preview_on_edit",
    ),
    path("<int:page_id>/view_draft/", preview.view_draft, name="view_draft"),
    path("<int:parent_page_id>/add_subpage/", create.add_subpage, name="add_subpage"),
    path("<int:page_id>/delete/", delete.delete, name="delete"),
    path("<int:page_id>/unpublish/", unpublish.unpublish, name="unpublish"),
    path(
        "<int:page_id>/convert_alias/",
        convert_alias.convert_alias,
        name="convert_alias",
    ),
    path("search/", search.search, name="search"),
    path("<int:page_to_move_id>/move/", move.move_choose_destination, name="move"),
    path(
        "<int:page_to_move_id>/move/<int:destination_id>/confirm/",
        move.move_confirm,
        name="move_confirm",
    ),
    path(
        "<int:page_to_move_id>/set_position/",
        ordering.set_page_position,
        name="set_page_position",
    ),
    path("<int:page_id>/copy/", copy.copy, name="copy"),
    path(
        "workflow/action/<int:page_id>/<slug:action_name>/<int:task_state_id>/",
        workflow.WorkflowAction.as_view(),
        name="workflow_action",
    ),
    path(
        "workflow/collect_action_data/<int:page_id>/<slug:action_name>/<int:task_state_id>/",
        workflow.CollectWorkflowActionData.as_view(),
        name="collect_workflow_action_data",
    ),
    path(
        "workflow/confirm_cancellation/<int:page_id>/",
        workflow.confirm_workflow_cancellation,
        name="confirm_workflow_cancellation",
    ),
    path(
        "workflow/preview/<int:page_id>/<int:task_id>/",
        workflow.preview_revision_for_task,
        name="workflow_preview",
    ),
    path(
        "workflow/status/<int:page_id>/",
        workflow.workflow_status,
        name="workflow_status",
    ),
    path(
        "moderation/<int:revision_id>/approve/",
        moderation.approve_moderation,
        name="approve_moderation",
    ),
    path(
        "moderation/<int:revision_id>/reject/",
        moderation.reject_moderation,
        name="reject_moderation",
    ),
    path(
        "moderation/<int:revision_id>/preview/",
        moderation.preview_for_moderation,
        name="preview_for_moderation",
    ),
    path("<int:page_id>/privacy/", page_privacy.set_privacy, name="set_privacy"),
    path("<int:page_id>/lock/", lock.lock, name="lock"),
    path("<int:page_id>/unlock/", lock.unlock, name="unlock"),
    path("<int:page_id>/revisions/", revisions.revisions_index, name="revisions_index"),
    path(
        "<int:page_id>/revisions/<int:revision_id>/view/",
        revisions.revisions_view,
        name="revisions_view",
    ),
    path(
        "<int:page_id>/revisions/<int:revision_id>/revert/",
        revisions.revisions_revert,
        name="revisions_revert",
    ),
    path(
        "<int:page_id>/revisions/<int:revision_id>/unschedule/",
        revisions.revisions_unschedule,
        name="revisions_unschedule",
    ),
    re_path(
        r"^(\d+)/revisions/compare/(live|earliest|\d+)\.\.\.(live|latest|\d+)/$",
        revisions.RevisionsCompare.as_view(),
        name="revisions_compare",
    ),
    path(
        "<int:page_id>/workflow_history/",
        history.workflow_history,
        name="workflow_history",
    ),
    path(
        "<int:page_id>/workflow_history/detail/<int:workflow_state_id>/",
        history.workflow_history_detail,
        name="workflow_history_detail",
    ),
    path("<int:page_id>/history/", history.PageHistoryView.as_view(), name="history"),
]
