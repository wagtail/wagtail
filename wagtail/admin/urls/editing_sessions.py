from django.urls import path

from wagtail.admin.views.editing_sessions import ping

app_name = "wagtailadmin_editing_sessions"
urlpatterns = [
    path(
        "ping/<str:app_label>/<str:model_name>/<str:object_id>/<int:session_id>/",
        ping,
        name="ping",
    ),
]
