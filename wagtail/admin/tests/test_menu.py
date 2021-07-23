from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from wagtail.admin.menu import AdminOnlyMenuItem, Menu, MenuItem, SubmenuMenuItem
from wagtail.admin.ui import sidebar
from wagtail.core import hooks
from wagtail.tests.utils import WagtailTestUtils


def menu_item_hook(*args, cls=MenuItem, **kwargs):
    def hook_fn():
        return cls(*args, **kwargs)

    return hook_fn


class TestMenuRendering(TestCase, WagtailTestUtils):
    def setUp(self):
        self.request = RequestFactory().get('/admin')
        self.request.user = self.create_superuser(username='admin')
        self.user = self.login()

    @override_settings(WAGTAIL_EXPERIMENTAL_FEATURES={"slim-sidebar"})
    def test_remember_collapsed(self):
        '''Sidebar should render with collapsed class applied.'''
        # Sidebar should not be collapsed
        self.client.cookies['wagtail_sidebar_collapsed'] = '0'
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertNotContains(response, 'sidebar-collapsed')

        # Sidebar should be collapsed
        self.client.cookies['wagtail_sidebar_collapsed'] = '1'
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertContains(response, 'sidebar-collapsed')

    @override_settings(WAGTAIL_EXPERIMENTAL_FEATURES={})
    def test_collapsed_only_with_feature_flag(self):
        '''Sidebar should only remember its collapsed state with the right feature flag set.'''
        # Sidebar should not be collapsed because the feature flag is not enabled
        self.client.cookies['wagtail_sidebar_collapsed'] = '1'
        response = self.client.get(reverse('wagtailadmin_home'))
        self.assertNotContains(response, 'sidebar-collapsed')

    def test_simple_menu(self):
        # Note: initialise the menu before registering hooks as this is what happens in reality.
        # (the real menus are initialised at the module level in admin/menu.py)
        menu = Menu(register_hook_name='register_menu_item')

        with hooks.register_temporarily([
            ('register_menu_item', menu_item_hook("Pages", '/pages/')),
            ('register_menu_item', menu_item_hook("Images", '/images/')),
        ]):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertListEqual(rendered, [
            sidebar.LinkMenuItem('pages', "Pages", '/pages/'),
            sidebar.LinkMenuItem('images', "Images", '/images/'),
        ])

    def test_menu_with_construct_hook(self):
        menu = Menu(register_hook_name='register_menu_item', construct_hook_name='construct_menu')

        def remove_images(request, items):
            items[:] = [item for item in items if not item.name == 'images']

        with hooks.register_temporarily([
            ('register_menu_item', menu_item_hook("Pages", '/pages/')),
            ('register_menu_item', menu_item_hook("Images", '/images/')),
            ('construct_menu', remove_images),
        ]):
            rendered = menu.render_component(self.request)

        self.assertEqual(
            rendered,
            [
                sidebar.LinkMenuItem('pages', "Pages", '/pages/'),
            ]
        )

    def test_submenu(self):
        menu = Menu(register_hook_name='register_menu_item')
        submenu = Menu(register_hook_name='register_submenu_item')

        with hooks.register_temporarily([
            ('register_menu_item', menu_item_hook("My lovely submenu", submenu, cls=SubmenuMenuItem)),
            ('register_submenu_item', menu_item_hook("Pages", '/pages/')),
        ]):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertEqual(len(rendered), 1)
        self.assertIsInstance(rendered[0], sidebar.SubMenuItem)
        self.assertEqual(rendered[0].name, "my-lovely-submenu")
        self.assertEqual(rendered[0].label, "My lovely submenu")
        self.assertListEqual(rendered[0].menu_items, [
            sidebar.LinkMenuItem('pages', "Pages", '/pages/'),
        ])

    def test_admin_only_menuitem(self):
        menu = Menu(register_hook_name='register_menu_item')

        with hooks.register_temporarily([
            ('register_menu_item', menu_item_hook("Pages", '/pages/')),
            ('register_menu_item', menu_item_hook("Secret pages", '/pages/secret/', cls=AdminOnlyMenuItem)),
        ]):
            rendered = menu.render_component(self.request)
            self.request.user = self.create_user(username='non-admin')
            rendered_non_admin = menu.render_component(self.request)

        self.assertListEqual(rendered, [
            sidebar.LinkMenuItem('pages', "Pages", '/pages/'),
            sidebar.LinkMenuItem('secret-pages', "Secret pages", '/pages/secret/'),
        ])

        self.assertListEqual(rendered_non_admin, [
            sidebar.LinkMenuItem('pages', "Pages", '/pages/'),
        ])
