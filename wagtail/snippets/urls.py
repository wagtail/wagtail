from django.urls import path

from wagtail.snippets.views import chooser, snippets

app_name = 'wagtailsnippets'
urlpatterns = [
    path('', snippets.index, name='index'),

    path('choose/', chooser.choose, name='choose_generic'),
    path('choose/<str:app_label>/<str:model_name>/', chooser.choose, name='choose'),
    path('choose/<str:app_label>/<str:model_name>/<str:pk>/', chooser.chosen, name='chosen'),

    path('<str:app_label>/<str:model_name>/', snippets.list, name='list'),
    path('<str:app_label>/<str:model_name>/add/', snippets.create, name='add'),
    path('<str:app_label>/<str:model_name>/<str:pk>/', snippets.edit, name='edit'),
    path('<str:app_label>/<str:model_name>/multiple/delete/', snippets.delete, name='delete-multiple'),
    path('<str:app_label>/<str:model_name>/<str:pk>/delete/', snippets.delete, name='delete'),
    path('<str:app_label>/<str:model_name>/<str:pk>/usage/', snippets.usage, name='usage'),
]
