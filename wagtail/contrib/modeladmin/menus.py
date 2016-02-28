from wagtail.wagtailadmin.menu import Menu, MenuItem, SubmenuMenuItem


class ModelAdminMenuItem(MenuItem):
    """
    A sub-class of wagtail's MenuItem, used by PageModelAdmin to add a link
    to its listing page
    """
    def __init__(self, modeladmin, order):
        self.modeladmin = modeladmin
        self.model = modeladmin.model
        self.opts = modeladmin.model._meta
        classnames = 'icon icon-%s' % modeladmin.get_menu_icon()
        super(ModelAdminMenuItem, self).__init__(
            label=modeladmin.get_menu_label(), url=modeladmin.get_index_url(),
            classnames=classnames, order=order)

    def is_shown(self, request):
        return self.modeladmin.show_menu_item(request)


class GroupMenuItem(SubmenuMenuItem):
    """
    A sub-class of wagtail's SubmenuMenuItem, used by ModelAdminGroup to add a
    link to the admin menu with its own submenu, linking to various listing
    pages
    """
    def __init__(self, modeladmingroup, order, menu):
        classnames = 'icon icon-%s' % modeladmingroup.get_menu_icon()
        super(GroupMenuItem, self).__init__(
            label=modeladmingroup.get_menu_label(), menu=menu,
            classnames=classnames, order=order, )

    def is_shown(self, request):
        """
        If there aren't any visible items in the submenu, don't bother to show
        this menu item
        """
        for menuitem in self.menu._registered_menu_items:
            if menuitem.is_shown(request):
                return True
        return False


class SubMenu(Menu):
    """
    A sub-class of wagtail's Menu, used by AppModelAdmin. We just want to
    override __init__, so that we can specify the items to include on
    initialisation
    """
    def __init__(self, menuitem_list):
        self._registered_menu_items = menuitem_list
        self.construct_hook_name = None
