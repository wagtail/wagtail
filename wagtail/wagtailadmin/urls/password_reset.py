from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailadmin.forms import PasswordResetForm
from wagtail.wagtailadmin.views import account

urlpatterns = [
    url(
        r'^$', account.password_reset, {
            'template_name': 'wagtailadmin/account/password_reset/form.html',
            'email_template_name': 'wagtailadmin/account/password_reset/email.txt',
            'subject_template_name': 'wagtailadmin/account/password_reset/email_subject.txt',
            'password_reset_form': PasswordResetForm,
            'post_reset_redirect': 'wagtailadmin_password_reset_done',
        }, name='wagtailadmin_password_reset'
    ),
    url(
        r'^done/$', account.password_reset_done, {
            'template_name': 'wagtailadmin/account/password_reset/done.html'
        }, name='wagtailadmin_password_reset_done'
    ),
    url(
        r'^confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        account.password_reset_confirm, {
            'template_name': 'wagtailadmin/account/password_reset/confirm.html',
            'post_reset_redirect': 'wagtailadmin_password_reset_complete',
        }, name='wagtailadmin_password_reset_confirm',
    ),
    url(
        r'^complete/$', account.password_reset_complete, {
            'template_name': 'wagtailadmin/account/password_reset/complete.html'
        }, name='wagtailadmin_password_reset_complete'
    ),
]
