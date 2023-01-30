from typing import Any, List, Mapping

from django import forms
from django.urls import reverse
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.telepath import Adapter, adapter


class BaseSidebarAdapter(Adapter):
    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/sidebar.js"),
            ]
        )


# Main menu


class MenuItem:
    def __init__(
        self,
        name: str,
        label: str,
        icon_name: str = "",
        classnames: str = "",
        attrs: Mapping[str, Any] = None,
    ):
        self.name = name
        self.label = label
        self.icon_name = icon_name
        self.classnames = classnames
        self.attrs = attrs or {}

    def js_args(self):
        return [
            {
                "name": self.name,
                "label": self.label,
                "icon_name": self.icon_name,
                "classnames": self.classnames,
                "attrs": self.attrs,
            }
        ]


@adapter("wagtail.sidebar.LinkMenuItem", base=BaseSidebarAdapter)
class LinkMenuItem(MenuItem):
    def __init__(
        self,
        name: str,
        label: str,
        url: str,
        icon_name: str = "",
        classnames: str = "",
        attrs: Mapping[str, Any] = None,
    ):
        super().__init__(
            name,
            label,
            icon_name=icon_name,
            classnames=classnames,
            attrs=attrs,
        )
        self.url = url

    def js_args(self):
        args = super().js_args()
        args[0]["url"] = self.url
        return args

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self.label == other.label
            and self.url == other.url
            and self.icon_name == other.icon_name
            and self.classnames == other.classnames
            and self.attrs == other.attrs
        )


@adapter("wagtail.sidebar.ActionMenuItem", base=BaseSidebarAdapter)
class ActionMenuItem(MenuItem):
    def __init__(
        self,
        name: str,
        label: str,
        action: str,
        icon_name: str = "",
        classnames: str = "",
        method: str = "POST",
        attrs: Mapping[str, Any] = None,
    ):
        super().__init__(
            name,
            label,
            icon_name=icon_name,
            classnames=classnames,
            attrs=attrs,
        )
        self.action = action
        self.method = method

    def js_args(self):
        args = super().js_args()
        args[0]["action"] = self.action
        args[0]["method"] = self.method
        return args

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self.label == other.label
            and self.action == other.action
            and self.method == other.method
            and self.icon_name == other.icon_name
            and self.classnames == other.classnames
            and self.attrs == other.attrs
        )


@adapter("wagtail.sidebar.SubMenuItem", base=BaseSidebarAdapter)
class SubMenuItem(MenuItem):
    def __init__(
        self,
        name: str,
        label: str,
        menu_items: List[MenuItem],
        icon_name: str = "",
        classnames: str = "",
        footer_text: str = "",
        attrs: Mapping[str, Any] = None,
    ):
        super().__init__(
            name,
            label,
            icon_name=icon_name,
            classnames=classnames,
            attrs=attrs,
        )
        self.menu_items = menu_items
        self.footer_text = footer_text

    def js_args(self):
        args = super().js_args()
        args[0]["footer_text"] = self.footer_text
        args.append(self.menu_items)
        return args

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self.label == other.label
            and self.menu_items == other.menu_items
            and self.icon_name == other.icon_name
            and self.classnames == other.classnames
            and self.footer_text == other.footer_text
            and self.attrs == other.attrs
        )


@adapter("wagtail.sidebar.PageExplorerMenuItem", base=BaseSidebarAdapter)
class PageExplorerMenuItem(LinkMenuItem):
    def __init__(
        self,
        name: str,
        label: str,
        url: str,
        start_page_id: int,
        icon_name: str = "",
        classnames: str = "",
        attrs: Mapping[str, Any] = None,
    ):
        super().__init__(
            name,
            label,
            url,
            icon_name=icon_name,
            classnames=classnames,
            attrs=attrs,
        )
        self.start_page_id = start_page_id

    def js_args(self):
        args = super().js_args()
        args.append(self.start_page_id)
        return args

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self.label == other.label
            and self.url == other.url
            and self.start_page_id == other.start_page_id
            and self.icon_name == other.icon_name
            and self.classnames == other.classnames
            and self.attrs == other.attrs
        )


# Modules


@adapter("wagtail.sidebar.WagtailBrandingModule", base=BaseSidebarAdapter)
class WagtailBrandingModule:
    def js_args(self):
        return [
            reverse("wagtailadmin_home"),
        ]


@adapter("wagtail.sidebar.SearchModule", base=BaseSidebarAdapter)
class SearchModule:
    def __init__(self, search_area):
        self.search_area = search_area

    def js_args(self):
        return [self.search_area.url]


@adapter("wagtail.sidebar.MainMenuModule", base=BaseSidebarAdapter)
class MainMenuModule:
    def __init__(
        self, menu_items: List[MenuItem], account_menu_items: List[MenuItem], user
    ):
        self.menu_items = menu_items
        self.account_menu_items = account_menu_items
        self.user = user

    def js_args(self):
        from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url

        try:
            first_name = self.user.first_name
        except AttributeError:
            first_name = None

        return [
            self.menu_items,
            self.account_menu_items,
            {
                "name": first_name or self.user.get_username(),
                "avatarUrl": avatar_url(self.user, size=50),
            },
        ]
