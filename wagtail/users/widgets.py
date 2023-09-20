from wagtail.admin.widgets import Button


class UserListingButton(Button):
    def __init__(self, label, url, classname="", **kwargs):
        if classname:
            classname += " button button-small"
        else:
            classname = "button button-small"
        super().__init__(label, url, classname=classname, **kwargs)
