from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode

from wagtail.admin.ui.menus import MenuItem


class PageMenuItem(MenuItem):
    url_name = None
    label = None
    icon_name = None
    priority = None
    link_rel = None

    def __init__(
        self,
        label=None,
        url=None,
        icon_name=None,
        priority=None,
        *,
        page,
        next_url=None,
    ):
        # Allow defining these as class attributes
        if label:
            self.label = label
        if url:
            self.url = url
        if icon_name:
            self.icon_name = icon_name
        if priority:
            self.priority = priority
        self.page = page
        self.next_url = next_url

    @cached_property
    def url(self):
        if self.url_name is not None:
            url = reverse(self.url_name, args=[self.page.id])
            if self.next_url:
                url += "?" + urlencode({"next": self.next_url})
            return url
