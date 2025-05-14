from warnings import warn

from django.forms.utils import flatatt
from django.utils.functional import cached_property

from wagtail import hooks
from wagtail.admin.ui.components import Component
from wagtail.admin.ui.menus import MenuItem
from wagtail.utils.deprecation import RemovedInWagtail80Warning


class BaseButton(Component):
    template_name = "wagtailadmin/shared/button.html"
    show = True
    label = ""
    icon_name = None
    url = None
    attrs = {}
    allow_in_dropdown = False

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
        self.priority = priority

    def get_context_data(self, parent_context):
        return {"button": self, "request": parent_context.get("request")}

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
        if not isinstance(other, (BaseButton, MenuItem)):
            return NotImplemented
        return (self.priority, self.label) < (other.priority, other.label)

    def __le__(self, other):
        if not isinstance(other, (BaseButton, MenuItem)):
            return NotImplemented
        return (self.priority, self.label) <= (other.priority, other.label)

    def __gt__(self, other):
        if not isinstance(other, (BaseButton, MenuItem)):
            return NotImplemented
        return (self.priority, self.label) > (other.priority, other.label)

    def __ge__(self, other):
        if not isinstance(other, (BaseButton, MenuItem)):
            return NotImplemented
        return (self.priority, self.label) >= (other.priority, other.label)

    def __eq__(self, other):
        if not isinstance(other, (BaseButton, MenuItem)):
            return NotImplemented
        return (
            self.label == other.label
            and self.url == other.url
            and self.classname == other.classname
            and self.attrs == other.attrs
            and self.priority == other.priority
        )

    @classmethod
    def from_menu_item(cls, menu_item: MenuItem):
        attrs = {}
        if link_rel := getattr(menu_item, "link_rel", None):
            attrs["rel"] = link_rel

        return cls(
            label=menu_item.label,
            url=menu_item.url,
            icon_name=menu_item.icon_name,
            priority=menu_item.priority,
            attrs=attrs,
        )


class Button(BaseButton):
    """Plain link button with a label and optional icon."""

    allow_in_dropdown = True


class HeaderButton(BaseButton):
    """Top-level button to be displayed after the breadcrumbs in the header."""

    def __init__(
        self,
        label="",
        url=None,
        classname="",
        icon_name=None,
        attrs={},
        icon_only=False,
        **kwargs,
    ):
        classname = f"{classname} w-header-button button".strip()
        attrs = attrs.copy()
        if icon_only:
            controller = f"{attrs.get('data-controller', '')} w-tooltip".strip()
            attrs["data-controller"] = controller
            attrs["data-w-tooltip-content-value"] = label
            attrs["aria-label"] = label
            label = ""

        super().__init__(
            label=label,
            url=url,
            classname=classname,
            icon_name=icon_name,
            attrs=attrs,
            **kwargs,
        )


# Base class for all listing buttons
# This is also used by SnippetListingButton defined in wagtail.snippets.widgets
class ListingButton(BaseButton):
    """Top-level button to be displayed in a listing view."""

    def __init__(self, label="", url=None, classname="", **kwargs):
        classname = f"{classname} button button-small button-secondary".strip()
        super().__init__(label=label, url=url, classname=classname, **kwargs)


class PageListingButton(ListingButton):
    def __init__(self, *args, **kwargs):
        warn(
            "`PageListingButton` is deprecated. "
            "Use `wagtail.admin.widgets.button.ListingButton` instead.",
            category=RemovedInWagtail80Warning,
        )
        super().__init__(*args, **kwargs)


class BaseDropdownMenuButton(BaseButton):
    template_name = "wagtailadmin/shared/button_with_dropdown.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, url=None, **kwargs)

    @cached_property
    def dropdown_buttons(self):
        raise NotImplementedError

    @property
    def base_attrs_string(self):
        attrs = self.attrs.copy()
        # For dropdowns, attrs are rendered on the wrapper `<div>`, not the
        # toggle button. Don't render the `aria-label` on the wrapper. We'll pass
        # it as the `title` context variable to be used as `toggle_aria_label`
        # instead, which will be rendered on the toggle button.
        attrs.pop("aria-label", None)
        return flatatt(attrs)

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context.update(
            {
                "buttons": sorted(self.dropdown_buttons),
                "label": self.label,
                "title": self.aria_label,
                "toggle_classname": self.classname,
                "icon_name": self.icon_name,
            }
        )
        return context


class ButtonWithDropdown(BaseDropdownMenuButton):
    def __init__(self, *args, **kwargs):
        self.dropdown_buttons = kwargs.pop("buttons", [])
        super().__init__(*args, **kwargs)


class ButtonWithDropdownFromHook(BaseDropdownMenuButton):
    # This page-specific class and template is documented for
    # the register_page_listing_buttons hook
    template_name = "wagtailadmin/pages/listing/_button_with_dropdown.html"

    def __init__(
        self,
        label,
        hook_name,
        page,
        user,
        next_url=None,
        **kwargs,
    ):
        self.hook_name = hook_name
        self.page = page
        self.user = user
        self.next_url = next_url

        super().__init__(label, **kwargs)

    @property
    def show(self):
        return bool(self.dropdown_buttons)

    @cached_property
    def dropdown_buttons(self):
        button_hooks = hooks.get_hooks(self.hook_name)

        hook_buttons = []
        for hook in button_hooks:
            hook_buttons.extend(
                hook(page=self.page, user=self.user, next_url=self.next_url)
            )

        buttons = []
        for button in hook_buttons:
            # Allow hooks to return either Button or MenuItem instances
            if isinstance(button, MenuItem):
                if button.is_shown(self.user):
                    buttons.append(Button.from_menu_item(button))
            elif button.show:
                buttons.append(button)

        return buttons
