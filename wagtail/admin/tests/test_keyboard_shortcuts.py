import json
import re
from unittest.mock import patch

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse

from wagtail.admin.templatetags.wagtailadmin_tags import get_wagtail_keyboard_actions
from wagtail.test.utils import WagtailTestUtils


class TestKeyboardShortcutsDialog(WagtailTestUtils, TestCase):
    def setUp(self):
        self.login()

    def test_keyboard_shortcuts_trigger_in_sidebar(self):
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)

        sidebar_data = (
            self.get_soup(response.content)
            .select_one("#wagtail-sidebar-props")
            .contents[0]
        )

        self.assertIn(
            json.dumps(
                {
                    "role": "button",
                    "data-a11y-dialog-show": "keyboard-shortcuts-dialog",
                    "data-action": "w-action#noop:prevent:stop",
                    "data-controller": "w-action",
                }
            ),
            sidebar_data,
        )

    def test_keyboard_shortcuts_dialog(self):
        response = self.client.get(reverse("wagtailadmin_home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/keyboard_shortcuts_dialog.html"
        )

        soup = self.get_soup(response.content)

        # Check that the keyboard shortcuts dialog is present
        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        self.assertIsNotNone(shortcuts_dialog)

        # Check that the keyboard shortcuts dialog has basic accessible content
        self.assertIn(
            "All keyboard shortcuts", shortcuts_dialog.find("caption").prettify()
        )
        self.assertIn("Keyboard shortcut", shortcuts_dialog.find("thead").prettify())

    def test_get_wagtail_keyboard_actions_with_comments(self):
        with patch(
            "wagtail.admin.templatetags.wagtailadmin_tags.get_comments_enabled",
            return_value=True,
        ):
            keyboard_keys = {"command/control": "Ctrl", "option/alt": "Alt"}
            actions = get_wagtail_keyboard_actions(keyboard_keys)

            self.assertIn(("Comments", "Ctrl + Alt + m"), actions)

    def test_get_wagtail_keyboard_actions_without_comments(self):
        with patch(
            "wagtail.admin.templatetags.wagtailadmin_tags.get_comments_enabled",
            return_value=False,
        ):
            keyboard_keys = {"command/control": "Ctrl", "option/alt": "Alt"}
            actions = get_wagtail_keyboard_actions(keyboard_keys)

            self.assertNotIn(("Comments", "Ctrl + Alt + m"), actions)


class TestMacKeyboardShortcutsDialog(WagtailTestUtils, TestCase):
    def setUp(self):
        # Creates a client with a Mac user agent
        self.client = Client(
            headers={
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
            }
        )
        self.login()

    def test_mac_useragent_and_behavior(self):
        response = self.client.get(reverse("wagtailadmin_home"))

        # Check that the user agent is a Mac
        user_agent = response.context["request"].headers.get("User-Agent", "")
        is_mac = re.search(r"Mac|iPod|iPhone|iPad", user_agent)

        # Add assertions based on expected Mac behavior
        self.assertTrue(is_mac)

        # Check that the keyboard shortcuts dialog has Mac-specific content
        soup = self.get_soup(response.content)
        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        all_shortcuts = shortcuts_dialog.select("kbd")
        for shortcut in all_shortcuts:
            # All shortcuts should have the ⌘ symbol
            self.assertIn("⌘", shortcut.prettify())
