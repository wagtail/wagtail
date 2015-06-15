from django.core import urlresolvers
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailsearch.urls import admin as admin_urls

from wagtail.wagtailadmin.menu import MenuItem


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^search/', include(admin_urls)),
    ]


class EditorsPicksMenuItem(MenuItem):
    def is_shown(self, request):
        # TEMPORARY: Only show if the user is a superuser
        return request.user.is_superuser

@hooks.register('register_settings_menu_item')
def register_editors_picks_menu_item():
    return EditorsPicksMenuItem(_('Promoted search results'), urlresolvers.reverse('wagtailsearch_editorspicks_index'), classnames='icon icon-pick', order=900)
