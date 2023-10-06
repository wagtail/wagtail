from warnings import warn

from django.forms.utils import flatatt
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail.coreutils import accepts_kwarg
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class Button(Component):
    show = True
    label = ""
    icon_name = None
    url = None
    attrs = {}

    def __init__(
        self, label="", url=None, classname="", icon_name=None, attrs={}, priority=1000
    ):
        if label:
            self.label = label

        if url:
            self.url = url

        self.classname = classname

        if icon_name:
            self.icon_name = icon_name

        self.attrs = self.attrs.copy()
        self.attrs.update(attrs)

        # if a 'title' attribute has been passed, correct that to aria-label
        # as that's what will be picked up in renderings that don't use button.render
        # directly (e.g. _dropdown_items.html)
        if "title" in self.attrs and "aria-label" not in self.attrs:
            self.attrs["aria-label"] = self.attrs.pop("title")
        self.priority = priority

    def render_html(self, parent_context=None):
        if hasattr(self, "template_name"):
            return super().render_html(parent_context)
        else:
            attrs = {
                "href": self.url,
                "class": self.classname,
            }
            attrs.update(self.attrs)
            return format_html("<a{}>{}</a>", flatatt(attrs), self.label)

    @property
    def base_attrs_string(self):
        # The set of attributes to be included on all renderings of
        # the button, as a string. Does not include the href or class
        # attributes (since the classnames intended for the button styling
        # should not be applied to dropdown items)
        return flatatt(self.attrs)

    @property
    def aria_label(self):
        return self.attrs.get("aria-label", "")

    def __repr__(self):
        return f"<Button: {self.label}>"

    def __lt__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) < (other.priority, other.label)

    def __le__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) <= (other.priority, other.label)

    def __gt__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) > (other.priority, other.label)

    def __ge__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) >= (other.priority, other.label)

    def __eq__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (
            self.label == other.label
            and self.url == other.url
            and self.classname == other.classname
            and self.attrs == other.attrs
            and self.priority == other.priority
        )


# Base class for all listing buttons
# This is also used by SnippetListingButton defined in wagtail.snippets.widgets
class ListingButton(Button):
    def __init__(self, label="", url=None, classname="", **kwargs):
        classname = f"{classname} button button-small button-secondary".strip()
        super().__init__(label=label, url=url, classname=classname, **kwargs)


class PageListingButton(ListingButton):
    aria_label_format = None
    url_name = None

    def __init__(self, *args, page=None, next_url=None, attrs={}, user=None, **kwargs):
        self.page = page
        self.user = user
        self.next_url = next_url

        attrs = attrs.copy()
        if (
            self.page
            and self.aria_label_format is not None
            and "aria-label" not in attrs
        ):
            attrs["aria-label"] = self.aria_label_format % {
                "title": self.page.get_admin_display_title()
            }
        super().__init__(*args, attrs=attrs, **kwargs)

    @cached_property
    def url(self):
        if self.page and self.url_name is not None:
            url = reverse(self.url_name, args=[self.page.id])
            if self.next_url:
                url += "?" + urlencode({"next": self.next_url})
            return url

    @cached_property
    def page_perms(self):
        if self.page:
            return self.page.permissions_for_user(self.user)


class BaseDropdownMenuButton(Button):
    template_name = "wagtailadmin/pages/listing/_button_with_dropdown.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, url=None, **kwargs)

    @cached_property
    def dropdown_buttons(self):
        raise NotImplementedError

    def get_context_data(self, parent_context):
        return {
            "buttons": sorted(self.dropdown_buttons),
            "label": self.label,
            "title": self.aria_label,
            "toggle_classname": self.classname,
            "icon_name": self.icon_name,
        }


class ButtonWithDropdown(BaseDropdownMenuButton):
    def __init__(self, *args, **kwargs):
        self.dropdown_buttons = kwargs.pop("buttons", [])
        super().__init__(*args, **kwargs)


class ButtonWithDropdownFromHook(BaseDropdownMenuButton):
    def __init__(
        self,
        label,
        hook_name,
        page,
        user=None,
        page_perms=None,
        next_url=None,
        **kwargs,
    ):
        self.hook_name = hook_name
        self.page = page

        if user is None:
            if page_perms is not None:
                warn(
                    "ButtonWithDropdownFromHook should be passed a `user` argument instead of `page_perms`",
                    category=RemovedInWagtail60Warning,
                    stacklevel=2,
                )
                self.user = page_perms.user
            else:
                raise TypeError("ButtonWithDropdownFromHook requires a `user` argument")
        else:
            self.user = user

        self.next_url = next_url

        super().__init__(label, **kwargs)

    @property
    def show(self):
        return bool(self.dropdown_buttons)

    @cached_property
    def dropdown_buttons(self):
        button_hooks = hooks.get_hooks(self.hook_name)

        buttons = []
        for hook in button_hooks:
            if accepts_kwarg(hook, "user"):
                buttons.extend(
                    hook(page=self.page, user=self.user, next_url=self.next_url)
                )
            else:
                # old-style hook that accepts page_perms instead of user
                warn(
                    f"`{self.hook_name}` hook functions should accept a `user` argument instead of `page_perms` -"
                    f" {hook.__module__}.{hook.__name__} needs to be updated",
                    category=RemovedInWagtail60Warning,
                )
                page_perms = self.page.permissions_for_user(self.user)
                buttons.extend(hook(self.page, page_perms, self.next_url))

        buttons = [b for b in buttons if b.show]
        return buttons
