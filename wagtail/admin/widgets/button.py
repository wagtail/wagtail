from functools import total_ordering

from django.forms.utils import flatatt
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.html import format_html

from wagtail.core import hooks


@total_ordering
class Button:
    show = True

    def __init__(self, label, url, classes=set(), attrs={}, priority=1000):
        self.label = label
        self.url = url
        self.classes = classes
        self.attrs = attrs.copy()
        self.priority = priority

    def render(self):
        attrs = {'href': self.url, 'class': ' '.join(sorted(self.classes))}
        attrs.update(self.attrs)
        return format_html('<a{}>{}</a>', flatatt(attrs), self.label)

    def __str__(self):
        return self.render()

    def __repr__(self):
        return '<Button: {}>'.format(self.label)

    def __lt__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.priority, self.label) < (other.priority, other.label)

    def __eq__(self, other):
        if not isinstance(other, Button):
            return NotImplemented
        return (self.label == other.label
                and self.url == other.url
                and self.classes == other.classes
                and self.attrs == other.attrs
                and self.priority == other.priority)


# Base class for all listing buttons
# This is also used by SnippetListingButton defined in wagtail.snippets.widgets
class ListingButton(Button):
    def __init__(self, label, url, classes=set(), **kwargs):
        classes = {'button', 'button-small', 'button-secondary'} | set(classes)
        super().__init__(label, url, classes=classes, **kwargs)


class PageListingButton(ListingButton):
    pass


class BaseDropdownMenuButton(Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, url=None, **kwargs)

    @cached_property
    def dropdown_buttons(self):
        raise NotImplementedError

    def render(self):
        return render_to_string(self.template_name, {
            'buttons': self.dropdown_buttons,
            'label': self.label,
            'title': self.attrs.get('title'),
            'is_parent': self.is_parent})


class ButtonWithDropdownFromHook(BaseDropdownMenuButton):
    template_name = 'wagtailadmin/pages/listing/_button_with_dropdown.html'

    def __init__(self, label, hook_name, page, page_perms, is_parent, next_url=None, **kwargs):
        self.hook_name = hook_name
        self.page = page
        self.page_perms = page_perms
        self.is_parent = is_parent
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
            buttons.extend(hook(self.page, self.page_perms, self.is_parent, self.next_url))

        buttons.sort()
        return buttons
