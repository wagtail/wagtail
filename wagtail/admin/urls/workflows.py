from django.urls import path

from wagtail.admin.views import workflows


app_name = 'wagtailadmin_workflows'
urlpatterns = [
    path('', workflows.Index.as_view(), name='index'),
    path('add/', workflows.Create.as_view(), name='add'),
    path('edit/<int:pk>/', workflows.Edit.as_view(), name='edit'),
    path('remove/<int:page_pk>/', workflows.remove_workflow, name='remove'),
    path('remove/<int:page_pk>/<int:workflow_pk>/', workflows.remove_workflow, name='remove'),
    path('add_to_page/<int:workflow_pk>/', workflows.add_to_page, name='add_to_page'),
    path('tasks/add/<str:app_label>/<str:model_name>/', workflows.CreateTask.as_view(), name='add_task'),
    path('tasks/select_type/', workflows.select_task_type, name='select_task_type'),
    path('tasks/index/', workflows.TaskIndex.as_view(), name='task_index'),
    path('tasks/edit/<int:pk>/', workflows.EditTask.as_view(), name='edit_task')
]
