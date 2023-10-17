from django.urls import path

from wagtail.admin.views.scheduled_pages import (
    publish,
    publish_confirm,
)

app_name = "wagtailadmin_scheduled_pages"

urlpatterns = [
    path("scheduled-pages/publish/<int:page_id>/", publish, name="publish_scheduled"),
    path("scheduled-pages/publish/<int:page_id>/confirm/", publish_confirm, name="publish_scheduled_confirm"),
]
