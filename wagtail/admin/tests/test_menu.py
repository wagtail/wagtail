from django.test import RequestFactory, TestCase
from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import (
    AdminOnlyMenuItem,
    DismissibleMenuItem,
    DismissibleSubmenuMenuItem,
    Menu,
    MenuItem,
    SubmenuMenuItem,
)
from wagtail.admin.ui import sidebar
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


def menu_item_hook(*args, cls=MenuItem, **kwargs):
    def hook_fn():
        return cls(*args, **kwargs)

    return hook_fn


class TestMenuRendering(TestCase, WagtailTestUtils):
    def setUp(self):
        self.request = RequestFactory().get("/admin")
        self.request.user = self.create_superuser(username="admin")
        self.profile = UserProfile.get_for_user(self.request.user)
        self.user = self.login()

    def test_remember_collapsed(self):
        """Sidebar should render with collapsed class applied."""
        # Sidebar should not be collapsed
        self.client.cookies["wagtail_sidebar_collapsed"] = "0"
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertNotContains(response, "sidebar-collapsed")

        # Sidebar should be collapsed
        self.client.cookies["wagtail_sidebar_collapsed"] = "1"
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertContains(response, "sidebar-collapsed")

    def test_simple_menu(self):
        # Note: initialise the menu before registering hooks as this is what happens in reality.
        # (the real menus are initialised at the module level in admin/menu.py)
        menu = Menu(register_hook_name="register_menu_item")

        with hooks.register_temporarily(
            [
                ("register_menu_item", menu_item_hook("Pages", "/pages/")),
                ("register_menu_item", menu_item_hook("Images", "/images/")),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertListEqual(
            rendered,
            [
                sidebar.LinkMenuItem("pages", "Pages", "/pages/"),
                sidebar.LinkMenuItem("images", "Images", "/images/"),
            ],
        )

    def test_menu_with_construct_hook(self):
        menu = Menu(
            register_hook_name="register_menu_item",
            construct_hook_name="construct_menu",
        )

        def remove_images(request, items):
            items[:] = [item for item in items if not item.name == "images"]

        with hooks.register_temporarily(
            [
                ("register_menu_item", menu_item_hook("Pages", "/pages/")),
                ("register_menu_item", menu_item_hook("Images", "/images/")),
                ("construct_menu", remove_images),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertEqual(
            rendered,
            [
                sidebar.LinkMenuItem("pages", "Pages", "/pages/"),
            ],
        )

    def test_submenu(self):
        menu = Menu(register_hook_name="register_menu_item")
        submenu = Menu(register_hook_name="register_submenu_item")

        with hooks.register_temporarily(
            [
                (
                    "register_menu_item",
                    menu_item_hook("My lovely submenu", submenu, cls=SubmenuMenuItem),
                ),
                ("register_submenu_item", menu_item_hook("Pages", "/pages/")),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertEqual(len(rendered), 1)
        self.assertIsInstance(rendered[0], sidebar.SubMenuItem)
        self.assertEqual(rendered[0].name, "my-lovely-submenu")
        self.assertEqual(rendered[0].label, "My lovely submenu")
        self.assertListEqual(
            rendered[0].menu_items,
            [
                sidebar.LinkMenuItem("pages", "Pages", "/pages/"),
            ],
        )

    def test_dismissible_initial(self):
        menu = Menu(register_hook_name="register_menu_item")
        submenu = Menu(register_hook_name="register_submenu_item")

        with hooks.register_temporarily(
            [
                (
                    "register_menu_item",
                    menu_item_hook(
                        "My dismissible submenu",
                        submenu,
                        cls=DismissibleSubmenuMenuItem,
                        name="dismissible-submenu-menu-item",
                    ),
                ),
                (
                    "register_submenu_item",
                    menu_item_hook(
                        "Pages",
                        "/pages/",
                        cls=DismissibleMenuItem,
                        name="dismissible-menu-item",
                    ),
                ),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertEqual(len(rendered), 1)
        self.assertIsInstance(rendered[0], sidebar.SubMenuItem)
        self.assertEqual(rendered[0].name, "dismissible-submenu-menu-item")
        self.assertEqual(rendered[0].label, "My dismissible submenu")
        self.assertEqual(
            rendered[0].attrs,
            # Should not be dismissed
            {"data-wagtail-dismissible-id": "dismissible-submenu-menu-item"},
        )
        self.assertListEqual(
            rendered[0].menu_items,
            [
                sidebar.LinkMenuItem(
                    "dismissible-menu-item",
                    "Pages",
                    "/pages/",
                    # Should not be dismissed
                    attrs={"data-wagtail-dismissible-id": "dismissible-menu-item"},
                ),
            ],
        )

    def test_dismissible_dismissed(self):
        self.profile.dismissibles = {
            "dismissible-submenu-menu-item": True,
            "dismissible-menu-item": True,
        }
        self.profile.save()
        self.request.user.refresh_from_db()

        menu = Menu(register_hook_name="register_menu_item")
        submenu = Menu(register_hook_name="register_submenu_item")

        with hooks.register_temporarily(
            [
                (
                    "register_menu_item",
                    menu_item_hook(
                        "My dismissible submenu",
                        submenu,
                        cls=DismissibleSubmenuMenuItem,
                        name="dismissible-submenu-menu-item",
                    ),
                ),
                (
                    "register_submenu_item",
                    menu_item_hook(
                        "Pages",
                        "/pages/",
                        cls=DismissibleMenuItem,
                        name="dismissible-menu-item",
                    ),
                ),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertEqual(len(rendered), 1)
        self.assertIsInstance(rendered[0], sidebar.SubMenuItem)
        self.assertEqual(rendered[0].name, "dismissible-submenu-menu-item")
        self.assertEqual(rendered[0].label, "My dismissible submenu")
        self.assertEqual(
            rendered[0].attrs,
            {
                "data-wagtail-dismissible-id": "dismissible-submenu-menu-item",
                # Should be dismissed
                "data-wagtail-dismissed": "",
            },
        )
        self.assertListEqual(
            rendered[0].menu_items,
            [
                sidebar.LinkMenuItem(
                    "dismissible-menu-item",
                    "Pages",
                    "/pages/",
                    # Should be dismissed
                    attrs={
                        "data-wagtail-dismissible-id": "dismissible-menu-item",
                        "data-wagtail-dismissed": "",
                    },
                ),
            ],
        )

    def test_dismissible_no_userprofile(self):
        # Without a user profile, dismissible menu items should not be dismissed
        self.profile.delete()
        self.request.user.refresh_from_db()

        menu = Menu(register_hook_name="register_menu_item")
        submenu = Menu(register_hook_name="register_submenu_item")

        with hooks.register_temporarily(
            [
                (
                    "register_menu_item",
                    menu_item_hook(
                        "My dismissible submenu",
                        submenu,
                        cls=DismissibleSubmenuMenuItem,
                        name="dismissible-submenu-menu-item",
                    ),
                ),
                (
                    "register_submenu_item",
                    menu_item_hook(
                        "Pages",
                        "/pages/",
                        cls=DismissibleMenuItem,
                        name="dismissible-menu-item",
                    ),
                ),
            ]
        ):
            rendered = menu.render_component(self.request)

        self.assertIsInstance(rendered, list)
        self.assertEqual(len(rendered), 1)
        self.assertIsInstance(rendered[0], sidebar.SubMenuItem)
        self.assertEqual(rendered[0].name, "dismissible-submenu-menu-item")
        self.assertEqual(rendered[0].label, "My dismissible submenu")
        self.assertEqual(
            rendered[0].attrs,
            {"data-wagtail-dismissible-id": "dismissible-submenu-menu-item"},
        )
        self.assertListEqual(
            rendered[0].menu_items,
            [
                sidebar.LinkMenuItem(
                    "dismissible-menu-item",
                    "Pages",
                    "/pages/",
                    attrs={"data-wagtail-dismissible-id": "dismissible-menu-item"},
                ),
            ],
        )

    def test_admin_only_menuitem(self):
        menu = Menu(register_hook_name="register_menu_item")

        with hooks.register_temporarily(
            [
                ("register_menu_item", menu_item_hook("Pages", "/pages/")),
                (
                    "register_menu_item",
                    menu_item_hook(
                        "Secret pages", "/pages/secret/", cls=AdminOnlyMenuItem
                    ),
                ),
            ]
        ):
            rendered = menu.render_component(self.request)
            self.request.user = self.create_user(username="non-admin")
            rendered_non_admin = menu.render_component(self.request)

        self.assertListEqual(
            rendered,
            [
                sidebar.LinkMenuItem("pages", "Pages", "/pages/"),
                sidebar.LinkMenuItem("secret-pages", "Secret pages", "/pages/secret/"),
            ],
        )

        self.assertListEqual(
            rendered_non_admin,
            [
                sidebar.LinkMenuItem("pages", "Pages", "/pages/"),
            ],
        )
