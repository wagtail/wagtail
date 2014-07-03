from django.core import urlresolvers
from django.conf import settings
from django.conf.urls import include, url
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin.menu import MenuItem

from wagtail.wagtailforms import urls
from wagtail.wagtailforms.models import get_forms_for_user

def register_admin_urls():
    return [
        url(r'^forms/', include(urls)),
    ]
hooks.register('register_admin_urls', register_admin_urls)

def construct_main_menu(request, menu_items):
    # show this only if the user has permission to retrieve submissions for at least one form
    if get_forms_for_user(request.user).exists():
        menu_items.append(
            MenuItem(_('Forms'), urlresolvers.reverse('wagtailforms_index'), classnames='icon icon-form', order=700)
        )
hooks.register('construct_main_menu', construct_main_menu)

def editor_js():
    return """<script src="%swagtailforms/js/page-editor.js"></script>""" % settings.STATIC_URL
hooks.register('insert_editor_js', editor_js)
