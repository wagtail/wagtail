from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin.ui.menus import MenuItem
from wagtail.admin.widgets.button import Button


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


def get_page_header_buttons(page, user, next_url, view_name):
    button_hooks = hooks.get_hooks("register_page_header_buttons")

    hook_buttons = []
    for hook in button_hooks:
        hook_buttons.extend(
            hook(page=page, user=user, next_url=next_url, view_name=view_name)
        )

    buttons = []
    for button in hook_buttons:
        # Allow hooks to return either Button or MenuItem instances
        if isinstance(button, MenuItem):
            if button.is_shown(user):
                buttons.append(Button.from_menu_item(button))
        elif button.show:
            buttons.append(button)
    return buttons
