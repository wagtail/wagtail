from django.urls import path

from wagtail.admin.views import account

urlpatterns = [
    path("", account.PasswordResetView.as_view(), name="wagtailadmin_password_reset"),
    path(
        "done/",
        account.PasswordResetDoneView.as_view(),
        name="wagtailadmin_password_reset_done",
    ),
    path(
        "confirm/<uidb64>/<token>/",
        account.PasswordResetConfirmView.as_view(),
        name="wagtailadmin_password_reset_confirm",
    ),
    path(
        "complete/",
        account.PasswordResetCompleteView.as_view(),
        name="wagtailadmin_password_reset_complete",
    ),
]
