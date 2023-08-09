from django.urls import path

from wagtail.contrib.search_promotions import views

app_name = "wagtailsearchpromotions"
urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add, name="add"),
    path("<int:query_id>/", views.edit, name="edit"),
    path("<int:query_id>/delete/", views.delete, name="delete"),
]
