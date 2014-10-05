from django.core import urlresolvers
from django.conf import settings
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailforms import urls
from wagtail.wagtailforms.models import get_forms_for_user

@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^forms/', include(urls)),
    ]

class FormsMenuItem(MenuItem):
    def is_shown(self, request):
        # show this only if the user has permission to retrieve submissions for at least one form
        return get_forms_for_user(request.user).exists()

@hooks.register('register_admin_menu_item')
def register_forms_menu_item():
    return FormsMenuItem(_('Forms'), urlresolvers.reverse('wagtailforms_index'), classnames='icon icon-form', order=700)


@hooks.register('insert_editor_js')
def editor_js():
    return """<script src="%swagtailforms/js/page-editor.js"></script>""" % settings.STATIC_URL
