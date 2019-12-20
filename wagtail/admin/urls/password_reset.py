from django.conf.urls import url

from wagtail.admin.views import account

urlpatterns = [
    url(
        r'^$', account.PasswordResetView.as_view(), name='wagtailadmin_password_reset'
    ),
    url(
        r'^done/$', account.PasswordResetDoneView.as_view(), name='wagtailadmin_password_reset_done'
    ),
    url(
        r'^confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        account.PasswordResetConfirmView.as_view(), name='wagtailadmin_password_reset_confirm',
    ),
    url(
        r'^complete/$', account.PasswordResetCompleteView.as_view(), name='wagtailadmin_password_reset_complete'
    ),
]
