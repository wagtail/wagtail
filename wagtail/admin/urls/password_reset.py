from django.urls import path, re_path

from wagtail.admin.views import account

urlpatterns = [
    path(
        '', account.PasswordResetView.as_view(), name='wagtailadmin_password_reset'
    ),
    path(
        'done/', account.PasswordResetDoneView.as_view(), name='wagtailadmin_password_reset_done'
    ),
    re_path(
        r'^confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        account.PasswordResetConfirmView.as_view(), name='wagtailadmin_password_reset_confirm',
    ),
    path(
        'complete/', account.PasswordResetCompleteView.as_view(), name='wagtailadmin_password_reset_complete'
    ),
]
