from unittest import TestCase

from django.test import TestCase as DjangoTestCase
from django.urls import reverse

from wagtail.admin.search import SearchArea
from wagtail.admin.ui.sidebar import (
    CustomBrandingModule, LinkMenuItem, MainMenuModule, PageExplorerMenuItem, SearchModule,
    SubMenuItem, WagtailBrandingModule)
from wagtail.core.telepath import JSContext
from wagtail.tests.utils import WagtailTestUtils


class TestAdaptLinkMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(LinkMenuItem('link', "Link", '/link/'))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.LinkMenuItem',
            '_args': [
                {
                    'classnames': '',
                    'icon_name': '',
                    'label': 'Link',
                    'name': 'link',
                    'url': '/link/'
                }
            ]
        })

    def test_adapt_with_classnames_and_icon(self):
        packed = JSContext().pack(LinkMenuItem('link', "Link", '/link/', icon_name='link-icon', classnames='some classes'))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.LinkMenuItem',
            '_args': [
                {
                    'classnames': 'some classes',
                    'icon_name': 'link-icon',
                    'label': 'Link',
                    'name': 'link',
                    'url': '/link/'
                }
            ]
        })


class TestAdaptSubMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(
            SubMenuItem('sub-menu', "Sub menu", [
                LinkMenuItem('link', "Link", '/link/', icon_name='link-icon'),
            ], footer_text='Footer text')
        )

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.SubMenuItem',
            '_args': [
                {
                    'name': 'sub-menu',
                    'label': 'Sub menu',
                    'icon_name': '',
                    'classnames': '',
                    'footer_text': 'Footer text'
                },
                [
                    {
                        '_type': 'wagtail.sidebar.LinkMenuItem',
                        '_args': [
                            {
                                'name': 'link',
                                'label': 'Link',
                                'icon_name': 'link-icon',
                                'classnames': '',
                                'url': '/link/'
                            }
                        ]
                    }
                ]
            ]
        })

    def test_adapt_without_footer_text(self):
        packed = JSContext().pack(
            SubMenuItem('sub-menu', "Sub menu", [
                LinkMenuItem('link', "Link", '/link/', icon_name='link-icon'),
            ])
        )

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.SubMenuItem',
            '_args': [
                {
                    'name': 'sub-menu',
                    'label': 'Sub menu',
                    'icon_name': '',
                    'classnames': '',
                    'footer_text': ''
                },
                [
                    {
                        '_type': 'wagtail.sidebar.LinkMenuItem',
                        '_args': [
                            {
                                'name': 'link',
                                'label': 'Link',
                                'icon_name': 'link-icon',
                                'classnames': '',
                                'url': '/link/'
                            }
                        ]
                    }
                ]
            ]
        })


class TestAdaptPageExplorerMenuItem(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(PageExplorerMenuItem('pages', "Pages", '/pages/', 1))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.PageExplorerMenuItem',
            '_args': [
                {
                    'classnames': '',
                    'icon_name': '',
                    'label': 'Pages',
                    'name': 'pages',
                    'url': '/pages/'
                },
                1
            ]
        })


class TestAdaptWagtailBrandingModule(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(WagtailBrandingModule())

        self.assertEqual(packed['_type'], 'wagtail.sidebar.WagtailBrandingModule')
        self.assertEqual(len(packed['_args']), 2)
        self.assertEqual(packed['_args'][0], reverse('wagtailadmin_home'))
        self.assertEqual(packed['_args'][1].keys(), {
            'desktopLogoBody',
            'desktopLogoEyeClosed',
            'desktopLogoEyeOpen',
            'desktopLogoTail',
            'mobileLogo'
        })


class TestAdaptCustomBrandingModule(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(CustomBrandingModule('<h1>My custom branding</h1>'))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.CustomBrandingModule',
            '_args': [
                '<h1>My custom branding</h1>',
                False
            ]
        })

    def test_collapsible(self):
        packed = JSContext().pack(CustomBrandingModule('<h1>My custom branding</h1>', collapsible=True))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.CustomBrandingModule',
            '_args': [
                '<h1>My custom branding</h1>',
                True
            ]
        })


class TestAdaptSearchModule(TestCase):
    def test_adapt(self):
        packed = JSContext().pack(SearchModule(SearchArea("Search", '/search/')))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.SearchModule',
            '_args': [
                '/search/'
            ]
        })


class TestAdaptMainMenuModule(DjangoTestCase, WagtailTestUtils):
    def test_adapt(self):
        main_menu = [
            LinkMenuItem('pages', "Pages", '/pages/'),
        ]
        account_menu = [
            LinkMenuItem('account', "Account", reverse('wagtailadmin_account'), icon_name='user'),
            LinkMenuItem('logout', "Logout", reverse('wagtailadmin_logout'), icon_name='logout'),
        ]
        user = self.create_user(username='admin')

        packed = JSContext().pack(MainMenuModule(main_menu, account_menu, user))

        self.assertEqual(packed, {
            '_type': 'wagtail.sidebar.MainMenuModule',
            '_args': [
                [
                    {
                        '_type': 'wagtail.sidebar.LinkMenuItem',
                        '_args': [
                            {'name': 'pages', 'label': 'Pages', 'icon_name': '', 'classnames': '', 'url': '/pages/'}
                        ]
                    }
                ],
                [
                    {
                        '_type': 'wagtail.sidebar.LinkMenuItem',
                        '_args': [
                            {'name': 'account', 'label': 'Account', 'icon_name': 'user', 'classnames': '', 'url': reverse('wagtailadmin_account')}
                        ]
                    },
                    {
                        '_type': 'wagtail.sidebar.LinkMenuItem',
                        '_args': [
                            {'name': 'logout', 'label': 'Logout', 'icon_name': 'logout', 'classnames': '', 'url': reverse('wagtailadmin_logout')}
                        ]
                    }
                ],
                {
                    'name': user.first_name or user.get_username(),
                    'avatarUrl': '//www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=100&d=mm'
                }
            ]
        })
