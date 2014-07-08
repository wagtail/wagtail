from django.conf.urls import url

from wagtail.wagtailadmin.forms import PasswordResetForm
from wagtail.wagtailadmin.views import account, chooser, home, pages, tags, userbar, page_privacy
from wagtail.wagtailcore import hooks


urlpatterns = [
    # Password reset
    url(
        r'^password_reset/$', 'django.contrib.auth.views.password_reset', {
            'template_name': 'wagtailadmin/account/password_reset/form.html',
            'email_template_name': 'wagtailadmin/account/password_reset/email.txt',
            'subject_template_name': 'wagtailadmin/account/password_reset/email_subject.txt',
            'password_reset_form': PasswordResetForm,
        }, name='password_reset'
    ),
    url(
        r'^password_reset/done/$', 'django.contrib.auth.views.password_reset_done', {
            'template_name': 'wagtailadmin/account/password_reset/done.html'
        }, name='password_reset_done'
    ),
    url(
        r'^password_reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'wagtailadmin/account/password_reset/confirm.html'},
        name='password_reset_confirm',
    ),
    url(
        r'^password_reset/complete/$', 'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'wagtailadmin/account/password_reset/complete.html'},
        name='password_reset_complete'
    ),
]

urlpatterns += [
    url(r'^$', home.home, name='wagtailadmin_home'),

    url(r'^failwhale/$', home.error_test, name='wagtailadmin_error_test'),

    url(r'^pages/$', pages.index, name='wagtailadmin_explore_root'),
    url(r'^pages/(\d+)/$', pages.index, name='wagtailadmin_explore'),

    url(r'^pages/new/(\w+)/(\w+)/(\d+)/$', pages.create, name='wagtailadmin_pages_create'),
    url(r'^pages/new/(\w+)/(\w+)/(\d+)/preview/$', pages.preview_on_create, name='wagtailadmin_pages_preview_on_create'),
    url(r'^pages/usage/(\w+)/(\w+)/$', pages.content_type_use, name='wagtailadmin_pages_type_use'),

    url(r'^pages/(\d+)/edit/$', pages.edit, name='wagtailadmin_pages_edit'),
    url(r'^pages/(\d+)/edit/preview/$', pages.preview_on_edit, name='wagtailadmin_pages_preview_on_edit'),

    url(r'^pages/preview/$', pages.preview, name='wagtailadmin_pages_preview'),
    url(r'^pages/preview_loading/$', pages.preview_loading, name='wagtailadmin_pages_preview_loading'),

    url(r'^pages/(\d+)/view_draft/$', pages.view_draft, name='wagtailadmin_pages_view_draft'),
    url(r'^pages/(\d+)/add_subpage/$', pages.add_subpage, name='wagtailadmin_pages_add_subpage'),
    url(r'^pages/(\d+)/delete/$', pages.delete, name='wagtailadmin_pages_delete'),
    url(r'^pages/(\d+)/unpublish/$', pages.unpublish, name='wagtailadmin_pages_unpublish'),

    url(r'^pages/search/$', pages.search, name='wagtailadmin_pages_search'),

    url(r'^pages/(\d+)/move/$', pages.move_choose_destination, name='wagtailadmin_pages_move'),
    url(r'^pages/(\d+)/move/(\d+)/$', pages.move_choose_destination, name='wagtailadmin_pages_move_choose_destination'),
    url(r'^pages/(\d+)/move/(\d+)/confirm/$', pages.move_confirm, name='wagtailadmin_pages_move_confirm'),
    url(r'^pages/(\d+)/set_position/$', pages.set_page_position, name='wagtailadmin_pages_set_page_position'),

    url(r'^pages/moderation/(\d+)/approve/$', pages.approve_moderation, name='wagtailadmin_pages_approve_moderation'),
    url(r'^pages/moderation/(\d+)/reject/$', pages.reject_moderation, name='wagtailadmin_pages_reject_moderation'),
    url(r'^pages/moderation/(\d+)/preview/$', pages.preview_for_moderation, name='wagtailadmin_pages_preview_for_moderation'),

    url(r'^pages/(\d+)/privacy/$', page_privacy.set_privacy, name='wagtailadmin_pages_set_privacy'),

    url(r'^choose-page/$', chooser.browse, name='wagtailadmin_choose_page'),
    url(r'^choose-page/(\d+)/$', chooser.browse, name='wagtailadmin_choose_page_child'),
    url(r'^choose-external-link/$', chooser.external_link, name='wagtailadmin_choose_page_external_link'),
    url(r'^choose-email-link/$', chooser.email_link, name='wagtailadmin_choose_page_email_link'),

    url(r'^tag-autocomplete/$', tags.autocomplete, name='wagtailadmin_tag_autocomplete'),

    url(r'^login/$', account.login, name='wagtailadmin_login'),
    url(r'^account/$', account.account, name='wagtailadmin_account'),
    url(r'^account/change_password/$', account.change_password, name='wagtailadmin_account_change_password'),
    url(r'^account/notification_preferences/$', account.notification_preferences, name='wagtailadmin_account_notification_preferences'),
    url(r'^logout/$', account.logout, name='wagtailadmin_logout'),

    url(r'^userbar/(\d+)/$', userbar.for_frontend, name='wagtailadmin_userbar_frontend'),
    url(r'^userbar/moderation/(\d+)/$', userbar.for_moderation, name='wagtailadmin_userbar_moderation'),
]


# This is here to make sure that 'django.contrib.auth.views.login' is reversed correctly
# It must be placed after 'wagtailadmin_login' to prevent this from being used
urlpatterns += [
    url(r'^login/$', 'django.contrib.auth.views.login'),
]


# Import additional urlpatterns from any apps that define a register_admin_urls hook
for fn in hooks.get_hooks('register_admin_urls'):
    urls = fn()
    if urls:
        urlpatterns += urls
