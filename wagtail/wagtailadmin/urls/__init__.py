from django.conf.urls import url, include
from django.views.decorators.cache import cache_control

from wagtail.wagtailadmin.urls import pages as wagtailadmin_pages_urls
from wagtail.wagtailadmin.urls import collections as wagtailadmin_collections_urls
from wagtail.wagtailadmin.urls import password_reset as wagtailadmin_password_reset_urls
from wagtail.wagtailadmin.views import account, chooser, home, pages, tags, userbar
from wagtail.wagtailcore import hooks
from wagtail.utils.urlpatterns import decorate_urlpatterns
from wagtail.wagtailadmin.decorators import require_admin_access


urlpatterns = [
    url(r'^$', home.home, name='wagtailadmin_home'),

    url(r'^failwhale/$', home.error_test, name='wagtailadmin_error_test'),

    url(r'^explorer-nav/$', pages.explorer_nav, name='wagtailadmin_explorer_nav'),

    # TODO: Move into wagtailadmin_pages namespace
    url(r'^pages/$', pages.index, name='wagtailadmin_explore_root'),
    url(r'^pages/(\d+)/$', pages.index, name='wagtailadmin_explore'),

    url(r'^pages/', include(wagtailadmin_pages_urls, app_name='wagtailadmin_pages', namespace='wagtailadmin_pages')),

    # TODO: Move into wagtailadmin_pages namespace
    url(r'^choose-page/$', chooser.browse, name='wagtailadmin_choose_page'),
    url(r'^choose-page/(\d+)/$', chooser.browse, name='wagtailadmin_choose_page_child'),
    url(r'^choose-page/search/$', chooser.search, name='wagtailadmin_choose_page_search'),
    url(r'^choose-external-link/$', chooser.external_link, name='wagtailadmin_choose_page_external_link'),
    url(r'^choose-email-link/$', chooser.email_link, name='wagtailadmin_choose_page_email_link'),

    url(r'^tag-autocomplete/$', tags.autocomplete, name='wagtailadmin_tag_autocomplete'),

    url(r'^collections/', include(wagtailadmin_collections_urls, namespace='wagtailadmin_collections')),

    url(r'^account/$', account.account, name='wagtailadmin_account'),
    url(r'^account/change_password/$', account.change_password, name='wagtailadmin_account_change_password'),
    url(
        r'^account/notification_preferences/$',
        account.notification_preferences,
        name='wagtailadmin_account_notification_preferences'
    ),
    url(r'^logout/$', account.logout, name='wagtailadmin_logout'),
]


# Import additional urlpatterns from any apps that define a register_admin_urls hook
for fn in hooks.get_hooks('register_admin_urls'):
    urls = fn()
    if urls:
        urlpatterns += urls


# Add "wagtailadmin.access_admin" permission check
urlpatterns = decorate_urlpatterns(urlpatterns, require_admin_access)


# These url patterns do not require an authenticated admin user
urlpatterns += [
    url(r'^login/$', account.login, name='wagtailadmin_login'),

    # These two URLs have the "permission_required" decorator applied directly
    # as they need to fail with a 403 error rather than redirect to the login page
    url(r'^userbar/(\d+)/$', userbar.for_frontend, name='wagtailadmin_userbar_frontend'),
    url(r'^userbar/moderation/(\d+)/$', userbar.for_moderation, name='wagtailadmin_userbar_moderation'),

    # Password reset
    url(r'^password_reset/', include(wagtailadmin_password_reset_urls)),
]

# Decorate all views with cache settings to prevent caching
urlpatterns = decorate_urlpatterns(
    urlpatterns,
    cache_control(private=True, no_cache=True, no_store=True, max_age=0)
)
