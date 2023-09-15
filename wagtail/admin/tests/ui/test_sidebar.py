from unittest import TestCase

from django.test import TestCase as DjangoTestCase
from django.urls import reverse

from wagtail.admin.search import SearchArea
from wagtail.admin.ui.sidebar import (
    ActionMenuItem,
    LinkMenuItem,
    MainMenuModule,
    PageExplorerMenuItem,
    SearchModule,
    SubMenuItem,
)
from wagtail.telepath import JSContext
from wagtail.test.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class TestAdaptLinkMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(LinkMenuItem("link", "Link", "/link/"))

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.LinkMenuItem",
                "_args": [
                    {
                        "classname": "",
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
                classname="some classes",
                attrs={"data-is-custom": "true"},
            )
        )

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.LinkMenuItem",
                "_args": [
                    {
                        "classname": "some classes",
                        "icon_name": "link-icon",
                        "label": "Link",
                        "name": "link",
                        "url": "/link/",
                        "attrs": {"data-is-custom": "true"},
                    }
                ],
            },
        )

    def test_adapt_with_deprecated_classnames(self):

        with self.assertWarnsRegex(
            RemovedInWagtail60Warning,
            "The `classnames` kwarg for sidebar LinkMenuItem is deprecated - use `classname` instead.",
        ):
            packed = JSContext().pack(
                LinkMenuItem("link", "Link", "/link/", classnames="legacy-classes")
            )

        self.assertEqual(
            packed,
            {
                "_type": "wagtail.sidebar.LinkMenuItem",
                "_args": [
                    {
                        "classname": "legacy-classes",  # mapped to new name but raises warning
                        "icon_name": "",
                        "label": "Link",
                        "name": "link",
                        "url": "/link/",
                        "attrs": {},
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
                        "classname": "",
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
                                    "classname": "",
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
                        "classname": "",
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
                                    "classname": "",
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
                        "classname": "",
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


class TestAdaptMainMenuModule(WagtailTestUtils, DjangoTestCase):
    def test_adapt(self):
        main_menu = [
            LinkMenuItem("pages", "Pages", "/pages/"),
        ]
        account_menu = [
            LinkMenuItem(
                "account", "Account", reverse("wagtailadmin_account"), icon_name="user"
            ),
            ActionMenuItem(
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
                                    "classname": "",
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
                                    "classname": "",
                                    "url": reverse("wagtailadmin_account"),
                                    "attrs": {},
                                }
                            ],
                        },
                        {
                            "_type": "wagtail.sidebar.ActionMenuItem",
                            "_args": [
                                {
                                    "name": "logout",
                                    "label": "Logout",
                                    "icon_name": "logout",
                                    "classname": "",
                                    "action": reverse("wagtailadmin_logout"),
                                    "method": "POST",
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
