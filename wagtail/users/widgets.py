from __future__ import absolute_import, unicode_literals

from wagtail.wagtailadmin.widgets import Button


class UserListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {'button', 'button-small', 'button-secondary'} | set(classes)
        super(UserListingButton, self).__init__(label, url, classes=classes, **kwargs)
