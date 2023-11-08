from wagtail.admin.widgets import Button


class UserListingButton(Button):
    def __init__(self, label, url, classname="", **kwargs):
        classname = f"{classname} button button-small".strip()
        super().__init__(label, url, classname=classname, **kwargs)
