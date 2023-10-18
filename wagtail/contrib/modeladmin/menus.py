from wagtail.admin.menu import MenuItem, SubmenuMenuItem


class ModelAdminMenuItem(MenuItem):
    """
    A sub-class of wagtail's MenuItem, used by PageModelAdmin to add a link
    to its listing page
    """

    def __init__(self, model_admin, order):
        self.model_admin = model_admin
        url = model_admin.url_helper.index_url
        menu_icon = model_admin.get_menu_icon()
        if menu_icon[:3] == "fa-":
            classname = "icon icon-%s" % menu_icon
            icon_name = None
        else:
            classname = ""
            icon_name = menu_icon
        super().__init__(
            label=model_admin.get_menu_label(),
            url=url,
            name=model_admin.get_menu_item_name(),
            classname=classname,
            icon_name=icon_name,
            order=order,
        )

    def is_shown(self, request):
        return self.model_admin.permission_helper.user_can_list(request.user)


class GroupMenuItem(SubmenuMenuItem):
    """
    A sub-class of wagtail's SubmenuMenuItem, used by ModelAdminGroup to add a
    link to the admin menu with its own submenu, linking to various listing
    pages
    """

    def __init__(self, modeladmingroup, order, menu):
        menu_icon = modeladmingroup.get_menu_icon()
        if menu_icon[:3] == "fa-":
            classname = "icon icon-%s" % menu_icon
            icon_name = None
        else:
            classname = ""
            icon_name = menu_icon
        super().__init__(
            label=modeladmingroup.get_menu_label(),
            menu=menu,
            name=modeladmingroup.get_menu_item_name(),
            classname=classname,
            icon_name=icon_name,
            order=order,
        )
