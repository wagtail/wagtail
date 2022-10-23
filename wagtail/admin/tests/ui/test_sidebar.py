from unittest import TestCase

from django.test import TestCase as DjangoTestCase
from django.urls import reverse

from wagtail.admin.search import SearchArea
from wagtail.admin.ui.sidebar import (
    LinkMenuItem,
    MainMenuModule,
    PageExplorerMenuItem,
    SearchModule,
    SubMenuItem,
)
from wagtail.telepath import JSContext
from wagtail.test.utils import WagtailTestUtils


class TestAdaptLinkMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(LinkMenuItem("link", "Link", "/link/"))

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.LinkMenuItem",
                "_args": [
                    {
                        "classnames": "",
                        "icon_name": "",
                        "label": "Link",
                        "name": "link",
                        "url": "/link/",
                        "attrs": {},
                    }
                ],
            },
        )

    def test_adapt_with_optional_parameters(self):
        packed = JSContext().pack(
            LinkMenuItem(
                "link",
                "Link",
                "/link/",
                icon_name="link-icon",
                classnames="some classes",
                attrs={"data-is-custom": "true"},
            )
        )

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.LinkMenuItem",
                "_args": [
                    {
                        "classnames": "some classes",
                        "icon_name": "link-icon",
                        "label": "Link",
                        "name": "link",
                        "url": "/link/",
                        "attrs": {"data-is-custom": "true"},
                    }
                ],
            },
        )


class TestAdaptSubMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(
            SubMenuItem(
                "sub-menu",
                "Sub menu",
                [
                    LinkMenuItem("link", "Link", "/link/", icon_name="link-icon"),
                ],
                footer_text="Footer text",
            )
        )

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.SubMenuItem",
                "_args": [
                    {
                        "name": "sub-menu",
                        "label": "Sub menu",
                        "icon_name": "",
                        "classnames": "",
                        "footer_text": "Footer text",
                        "attrs": {},
                    },
                    [
                        {
                            "_type": "wagtail.sidebar.LinkMenuItem",
                            "_args": [
                                {
                                    "name": "link",
                                    "label": "Link",
                                    "icon_name": "link-icon",
                                    "classnames": "",
                                    "url": "/link/",
                                    "attrs": {},
                                }
                            ],
                        }
                    ],
                ],
            },
        )

    def test_adapt_without_footer_text(self):
        packed = JSContext().pack(
            SubMenuItem(
                "sub-menu",
                "Sub menu",
                [
                    LinkMenuItem("link", "Link", "/link/", icon_name="link-icon"),
                ],
            )
        )

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.SubMenuItem",
                "_args": [
                    {
                        "name": "sub-menu",
                        "label": "Sub menu",
                        "icon_name": "",
                        "classnames": "",
                        "footer_text": "",
                        "attrs": {},
                    },
                    [
                        {
                            "_type": "wagtail.sidebar.LinkMenuItem",
                            "_args": [
                                {
                                    "name": "link",
                                    "label": "Link",
                                    "icon_name": "link-icon",
                                    "classnames": "",
                                    "url": "/link/",
                                    "attrs": {},
                                }
                            ],
                        }
                    ],
                ],
            },
        )


class TestAdaptPageExplorerMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(PageExplorerMenuItem("pages", "Pages", "/pages/", 1))

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.PageExplorerMenuItem",
                "_args": [
                    {
                        "attrs": {},
                        "classnames": "",
                        "icon_name": "",
                        "label": "Pages",
                        "name": "pages",
                        "url": "/pages/",
                    },
                    1,
                ],
            },
        )


class TestAdaptSearchModule(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(SearchModule(SearchArea("Search", "/search/")))

        self.assertEqual(
            packed, {"_type": "wagtail.sidebar.SearchModule", "_args": ["/search/"]}
        )


class TestAdaptMainMenuModule(DjangoTestCase, WagtailTestUtils):
    def test_adapt(self):
        main_menu = [
            LinkMenuItem("pages", "Pages", "/pages/"),
        ]
        account_menu = [
            LinkMenuItem(
                "account", "Account", reverse("wagtailadmin_account"), icon_name="user"
            ),
            LinkMenuItem(
                "logout", "Logout", reverse("wagtailadmin_logout"), icon_name="logout"
            ),
        ]
        user = self.create_user(username="admin")

        packed = JSContext().pack(MainMenuModule(main_menu, account_menu, user))

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.MainMenuModule",
                "_args": [
                    [
                        {
                            "_type": "wagtail.sidebar.LinkMenuItem",
                            "_args": [
                                {
                                    "name": "pages",
                                    "label": "Pages",
                                    "icon_name": "",
                                    "classnames": "",
                                    "url": "/pages/",
                                    "attrs": {},
                                }
                            ],
                        }
                    ],
                    [
                        {
                            "_type": "wagtail.sidebar.LinkMenuItem",
                            "_args": [
                                {
                                    "name": "account",
                                    "label": "Account",
                                    "icon_name": "user",
                                    "classnames": "",
                                    "url": reverse("wagtailadmin_account"),
                                    "attrs": {},
                                }
                            ],
                        },
                        {
                            "_type": "wagtail.sidebar.LinkMenuItem",
                            "_args": [
                                {
                                    "name": "logout",
                                    "label": "Logout",
                                    "icon_name": "logout",
                                    "classnames": "",
                                    "url": reverse("wagtailadmin_logout"),
                                    "attrs": {},
                                }
                            ],
                        },
                    ],
                    {
                        "name": user.first_name or user.get_username(),
                        "avatarUrl": "//www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=100&d=mm",
                    },
                ],
            },
        )
