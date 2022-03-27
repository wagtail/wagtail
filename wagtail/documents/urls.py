from django.urls import path, re_path

from wagtail.documents.views import serve

urlpatterns = [
    re_path(r"^(\d+)/(.*)$", serve.serve, name="wagtaildocs_serve"),
    path(
        "authenticate_with_password/<int:restriction_id>/",
        serve.authenticate_with_password,
        name="wagtaildocs_authenticate_with_password",
    ),
]
