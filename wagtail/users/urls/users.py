from django.urls import path

from wagtail.users.views import users

app_name = "wagtailusers_users"
urlpatterns = [
    path("", users.Index.as_view(), name="index"),
    path("add/", users.Create.as_view(), name="add"),
    path("<str:user_id>/", users.edit, name="edit"),
    path("<str:pk>/delete/", users.Delete.as_view(), name="delete"),
]
