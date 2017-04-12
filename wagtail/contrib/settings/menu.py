from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse

from wagtail.wagtailadmin.menu import MenuItem

from .permissions import user_can_edit_setting_type


class SettingMenuItem(MenuItem):
    def __init__(self, model_admin, order):
        self.model_admin = model_admin
        self.model = model_admin.model

        icon_classes = 'icon icon-' + model_admin.get_menu_icon()

        super(SettingMenuItem, self).__init__(
            label=model_admin.get_menu_label(),
            url=reverse(model_admin.edit_url_name),
            classnames=icon_classes)

    def is_shown(self, request):
        return user_can_edit_setting_type(request.user, self.model)
