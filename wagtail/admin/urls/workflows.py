from django.urls import path

from wagtail.admin.views import workflows


app_name = 'wagtailadmin_workflows'
urlpatterns = [
    path('workflows/', workflows.Index.as_view(), name='index'),
    path('workflows/add/', workflows.Create.as_view(), name='add'),
    path('workflows/enable/<int:pk>/', workflows.enable_workflow, name='enable'),
    path('workflows/disable/<int:pk>/', workflows.Disable.as_view(), name='disable'),
    path('workflows/edit/<int:pk>/', workflows.Edit.as_view(), name='edit'),
    path('workflows/remove/<int:page_pk>/', workflows.remove_workflow, name='remove'),
    path('workflows/remove/<int:page_pk>/<int:workflow_pk>/', workflows.remove_workflow, name='remove'),
    path('tasks/add/<str:app_label>/<str:model_name>/', workflows.CreateTask.as_view(), name='add_task'),
    path('tasks/select_type/', workflows.select_task_type, name='select_task_type'),
    path('tasks/index/', workflows.TaskIndex.as_view(), name='task_index'),
    path('tasks/edit/<int:pk>/', workflows.EditTask.as_view(), name='edit_task'),
    path('tasks/disable/<int:pk>/', workflows.DisableTask.as_view(), name='disable_task'),
    path('tasks/enable/<int:pk>/', workflows.enable_task, name='enable_task'),
    path('task_chooser/', workflows.task_chooser, name='task_chooser'),
    path('task_chooser/<int:task_id>/', workflows.task_chosen, name='task_chosen'),
]
