from wagtail.admin.widgets import Button


class UserListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {"button", "button-small"} | set(classes)
        super().__init__(label, url, classes=classes, **kwargs)
