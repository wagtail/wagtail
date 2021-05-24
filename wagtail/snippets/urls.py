from django.urls import path

from wagtail.snippets.views import chooser, snippets


app_name = 'wagtailsnippets'
urlpatterns = [
    path('', snippets.index, name='index'),

    path('choose/', chooser.choose, name='choose_generic'),
    path('choose/<slug:app_label>/<slug:model_name>/', chooser.choose, name='choose'),
    path('choose/<slug:app_label>/<slug:model_name>/<str:pk>/', chooser.chosen, name='chosen'),

    path('<slug:app_label>/<slug:model_name>/', snippets.list, name='list'),
    path('<slug:app_label>/<slug:model_name>/add/', snippets.create, name='add'),
    path('<slug:app_label>/<slug:model_name>/edit/<str:pk>/', snippets.edit, name='edit'),
    path('<slug:app_label>/<slug:model_name>/multiple/delete/', snippets.delete, name='delete-multiple'),
    path('<slug:app_label>/<slug:model_name>/delete/<str:pk>/', snippets.delete, name='delete'),
    path('<slug:app_label>/<slug:model_name>/usage/<str:pk>/', snippets.usage, name='usage'),

    # legacy URLs that could potentially collide if the pk matches one of the reserved names above
    # ('add', 'edit' etc) - redirect to the unambiguous version
    path('<slug:app_label>/<slug:model_name>/<str:pk>/', snippets.redirect_to_edit),
    path('<slug:app_label>/<slug:model_name>/<str:pk>/delete/', snippets.redirect_to_delete),
    path('<slug:app_label>/<slug:model_name>/<str:pk>/usage/', snippets.redirect_to_usage),
]
