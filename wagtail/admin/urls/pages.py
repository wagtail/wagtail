from django.urls import path, re_path

from wagtail.admin.views import page_privacy, pages

app_name = 'wagtailadmin_pages'
urlpatterns = [
    path('add/<slug:content_type_app_name>/<slug:content_type_model_name>/<int:parent_page_id>/', pages.create, name='add'),
    path('add/<slug:content_type_app_name>/<slug:content_type_model_name>/<int:parent_page_id>/preview/', pages.PreviewOnCreate.as_view(), name='preview_on_add'),
    path('usage/<slug:content_type_app_name>/<slug:content_type_model_name>/', pages.content_type_use, name='type_use'),

    path('<int:page_id>/edit/', pages.edit, name='edit'),
    path('<int:page_id>/edit/preview/', pages.PreviewOnEdit.as_view(), name='preview_on_edit'),

    path('<int:page_id>/view_draft/', pages.view_draft, name='view_draft'),
    path('<int:parent_page_id>/add_subpage/', pages.add_subpage, name='add_subpage'),
    path('<int:page_id>/delete/', pages.delete, name='delete'),
    path('<int:page_id>/unpublish/', pages.unpublish, name='unpublish'),

    path('search/', pages.search, name='search'),

    path('<int:page_to_move_id>/move/', pages.move_choose_destination, name='move'),
    path('<int:page_to_move_id>/move/<int:viewed_page_id>/', pages.move_choose_destination, name='move_choose_destination'),
    path('<int:page_to_move_id>/move/<int:destination_id>/confirm/', pages.move_confirm, name='move_confirm'),
    path('<int:page_to_move_id>/set_position/', pages.set_page_position, name='set_page_position'),

    path('<int:page_id>/copy/', pages.copy, name='copy'),

    path('workflow/action/<int:page_id>/<slug:action_name>/<int:task_state_id>/', pages.WorkflowAction.as_view(), name='workflow_action'),
    path('workflow/collect_action_data/<int:page_id>/<slug:action_name>/<int:task_state_id>/', pages.CollectWorkflowActionData.as_view(), name='collect_workflow_action_data'),
    path('workflow/confirm_cancellation/<int:page_id>/', pages.confirm_workflow_cancellation, name='confirm_workflow_cancellation'),
    path('workflow/preview/<int:page_id>/<int:task_id>/', pages.preview_revision_for_task, name='workflow_preview'),
    path('workflow/status/<int:page_id>/', pages.workflow_status, name='workflow_status'),

    path('moderation/<int:revision_id>/approve/', pages.approve_moderation, name='approve_moderation'),
    path('moderation/<int:revision_id>/reject/', pages.reject_moderation, name='reject_moderation'),
    path('moderation/<int:revision_id>/preview/', pages.preview_for_moderation, name='preview_for_moderation'),

    path('<int:page_id>/privacy/', page_privacy.set_privacy, name='set_privacy'),

    path('<int:page_id>/lock/', pages.lock, name='lock'),
    path('<int:page_id>/unlock/', pages.unlock, name='unlock'),

    path('<int:page_id>/revisions/', pages.revisions_index, name='revisions_index'),
    path('<int:page_id>/revisions/<int:revision_id>/view/', pages.revisions_view, name='revisions_view'),
    path('<int:page_id>/revisions/<int:revision_id>/revert/', pages.revisions_revert, name='revisions_revert'),
    path('<int:page_id>/revisions/<int:revision_id>/unschedule/', pages.revisions_unschedule, name='revisions_unschedule'),
    re_path(r'^(\d+)/revisions/compare/(live|earliest|\d+)\.\.\.(live|latest|\d+)/$', pages.revisions_compare, name='revisions_compare'),

    path('<int:page_id>/workflow_history/', pages.workflow_history, name='workflow_history'),
    path('<int:page_id>/workflow_history/detail/<int:workflow_state_id>/', pages.workflow_history_detail, name='workflow_history_detail'),

    path('<int:page_id>/history/', pages.PageHistoryView.as_view(), name='history'),
]
