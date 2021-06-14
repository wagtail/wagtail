from typing import List

from django import forms
from django.urls import reverse
from django.utils.functional import cached_property

from wagtail.admin.staticfiles import versioned_static
from wagtail.core.telepath import Adapter, adapter


class BaseSidebarAdapter(Adapter):
    @cached_property
    def media(self):
        return forms.Media(js=[
            versioned_static('wagtailadmin/js/sidebar.js'),
        ])


# Main menu

class MenuItem:
    def __init__(self, name: str, label: str, icon_name: str = '', classnames: str = ''):
        self.name = name
        self.label = label
        self.icon_name = icon_name
        self.classnames = classnames

    def js_args(self):
        return [
            {
                'name': self.name,
                'label': self.label,
                'icon_name': self.icon_name,
                'classnames': self.classnames,
            }
        ]


@adapter('wagtail.sidebar.LinkMenuItem', base=BaseSidebarAdapter)
class LinkMenuItem(MenuItem):
    def __init__(self, name: str, label: str, url: str, icon_name: str = '', classnames: str = ''):
        super().__init__(name, label, icon_name=icon_name, classnames=classnames)
        self.url = url

    def js_args(self):
        args = super().js_args()
        args[0]['url'] = self.url
        return args

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.name == other.name
            and self.label == other.label
            and self.url == other.url
            and self.icon_name == other.icon_name
            and self.classnames == other.classnames
        )


@adapter('wagtail.sidebar.SubMenuItem', base=BaseSidebarAdapter)
class SubMenuItem(MenuItem):
    def __init__(self, name: str, label: str, menu_items: List[MenuItem], icon_name: str = '', classnames: str = '', footer_text: str = ''):
        super().__init__(name, label, icon_name=icon_name, classnames=classnames)
        self.menu_items = menu_items
        self.footer_text = footer_text

    def js_args(self):
        args = super().js_args()
        args[0]['footer_text'] = self.footer_text
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
        )


@adapter('wagtail.sidebar.PageExplorerMenuItem', base=BaseSidebarAdapter)
class PageExplorerMenuItem(LinkMenuItem):
    def __init__(self, name: str, label: str, url: str, start_page_id: int, icon_name: str = '', classnames: str = ''):
        super().__init__(name, label, url, icon_name=icon_name, classnames=classnames)
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
        )


# Modules

@adapter('wagtail.sidebar.WagtailBrandingModule', base=BaseSidebarAdapter)
class WagtailBrandingModule:
    def js_args(self):
        return [
            reverse('wagtailadmin_home'),
            {
                'mobileLogo': versioned_static('wagtailadmin/images/wagtail-logo.svg'),
                'desktopLogoBody': versioned_static('wagtailadmin/images/logo-body.svg'),
                'desktopLogoTail': versioned_static('wagtailadmin/images/logo-tail.svg'),
                'desktopLogoEyeOpen': versioned_static('wagtailadmin/images/logo-eyeopen.svg'),
                'desktopLogoEyeClosed': versioned_static('wagtailadmin/images/logo-eyeclosed.svg'),
            }
        ]


@adapter('wagtail.sidebar.CustomBrandingModule', base=BaseSidebarAdapter)
class CustomBrandingModule:
    def __init__(self, html, collapsible=False):
        self.html = html
        self.collapsible = collapsible

    def js_args(self):
        return [
            self.html,
            self.collapsible,
        ]


@adapter('wagtail.sidebar.SearchModule', base=BaseSidebarAdapter)
class SearchModule:
    def __init__(self, search_area):
        self.search_area = search_area

    def js_args(self):
        return [
            self.search_area.url
        ]


@adapter('wagtail.sidebar.MainMenuModule', base=BaseSidebarAdapter)
class MainMenuModule:
    def __init__(self, menu_items: List[MenuItem], account_menu_items: List[MenuItem], user):
        self.menu_items = menu_items
        self.account_menu_items = account_menu_items
        self.user = user

    def js_args(self):
        from wagtail.admin.templatetags.wagtailadmin_tags import avatar_url

        return [
            self.menu_items,
            self.account_menu_items,
            {
                'name': self.user.first_name or self.user.get_username(),
                'avatarUrl': avatar_url(self.user, size=50),
            }
        ]
