from django.urls import path

from wagtail.admin.views.editing_sessions import ping, release

app_name = "wagtailadmin_editing_sessions"
urlpatterns = [
    path(
        "ping/<str:app_label>/<str:model_name>/<str:object_id>/<int:session_id>/",
        ping,
        name="ping",
    ),
    path(
        "release/<int:session_id>/",
        release,
        name="release",
    ),
]
