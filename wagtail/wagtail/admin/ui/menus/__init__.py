class MenuItem:
    """
    Describes a simple menu item in the Wagtail admin interface, which may be
    used in different contexts, e.g. inside dropdowns or as a standalone item.
    This class does not define how it should be rendered; that is up to the menu
    renderer to use the description provided here.
    """

    def __init__(self, label: str, url: str, icon_name="", priority=1000):
        self.label = label
        self.url = url
        self.icon_name = icon_name
        self.priority = priority

    def is_shown(self, user):
        """
        Whether this menu item should be shown for the given user; permission
        checks etc. should go here. By default, menu items are shown all the time.
        """
        return True

    def __lt__(self, other):
        if not isinstance(other, MenuItem):
            return NotImplemented
        return (self.priority, self.label) < (other.priority, other.label)
