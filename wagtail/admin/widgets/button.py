from django.forms.utils import flatatt
from django.utils.functional import cached_property
from django.utils.html import format_html

from wagtail import hooks
from wagtail.admin.ui.components import Component


class Button(Component):
    show = True

    def __init__(
        self, label, url, classes=set(), icon_name=None, attrs={}, priority=1000
    ):
        self.label = label
        self.url = url
        self.classes = classes
        self.icon_name = icon_name
        self.attrs = attrs.copy()
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
                "class": " ".join(sorted(self.classes)),
            }
            attrs.update(self.attrs)
            return format_html("<a{}>{}</a>", flatatt(attrs), self.label)

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
            and self.classes == other.classes
            and self.attrs == other.attrs
            and self.priority == other.priority
        )


# Base class for all listing buttons
# This is also used by SnippetListingButton defined in wagtail.snippets.widgets
class ListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {"button", "button-small", "button-secondary"} | set(classes)
        super().__init__(label, url, classes=classes, **kwargs)


class PageListingButton(ListingButton):
    pass


class BaseDropdownMenuButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, url=None, **kwargs)

    @cached_property
    def dropdown_buttons(self):
        raise NotImplementedError

    def get_context_data(self, parent_context):
        return {
            "buttons": self.dropdown_buttons,
            "label": self.label,
            "title": self.aria_label,
            "classes": self.classes,
            "icon_name": self.icon_name,
        }


class ButtonWithDropdown(BaseDropdownMenuButton):
    template_name = "wagtailadmin/pages/listing/_button_with_dropdown.html"

    def __init__(self, *args, **kwargs):
        self.dropdown_buttons = kwargs.pop("buttons", [])
        super().__init__(*args, **kwargs)


class ButtonWithDropdownFromHook(BaseDropdownMenuButton):
    template_name = "wagtailadmin/pages/listing/_button_with_dropdown.html"

    def __init__(self, label, hook_name, page, page_perms, next_url=None, **kwargs):
        self.hook_name = hook_name
        self.page = page
        self.page_perms = page_perms
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
            buttons.extend(hook(self.page, self.page_perms, self.next_url))

        buttons.sort()
        return buttons
