from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _

from wagtail.admin.menu import MenuItem
from wagtail.contrib.forms import urls
from wagtail.contrib.forms.utils import get_forms_for_user
from wagtail.core import hooks


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        path('forms/', include(urls, namespace='wagtailforms')),
    ]


class FormsMenuItem(MenuItem):
    def is_shown(self, request):
        # show this only if the user has permission to retrieve submissions for at least one form
        return get_forms_for_user(request.user).exists()


@hooks.register('register_admin_menu_item')
def register_forms_menu_item():
    return FormsMenuItem(
        _('Forms'), reverse('wagtailforms:index'),
        name='forms', icon_name='form', order=700
    )
