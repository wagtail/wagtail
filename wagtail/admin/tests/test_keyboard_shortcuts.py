import json
import re

from django.test import RequestFactory, TestCase, override_settings
from django.test.client import Client
from django.urls import reverse

from wagtail.admin.utils import get_keyboard_key_labels_from_request
from wagtail.test.utils import WagtailTestUtils
from wagtail.users.models import UserProfile


class TestGetKeyboardKeyLabelsFromRequestUtil(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()

    def test_get_keyboard_key_labels_for_default(self):
        """
        Test the default case for keyboard key labels where no User-Agent is provided.
        This simulates an edge case where the request does not contain a User-Agent.
        """
        request = self.factory.get("/")
        key_labels = get_keyboard_key_labels_from_request(request)

        self.assertEqual(key_labels.ALT, "Alt")
        self.assertEqual(key_labels.CMD, "Ctrl")
        self.assertEqual(key_labels.CTRL, "Ctrl")
        self.assertEqual(key_labels.MOD, "Ctrl")

    def test_get_keyboard_key_labels_for_mac_os(self):
        """
        Test the keyboard key labels with a Mac user agent.
        """
        self.client.defaults["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        )
        response = self.client.get(reverse("wagtailadmin_home"))

        key_labels = get_keyboard_key_labels_from_request(response.wsgi_request)

        self.assertEqual(key_labels.ALT, "⌥")
        self.assertEqual(key_labels.CMD, "⌘")
        self.assertEqual(key_labels.CTRL, "^")
        self.assertEqual(key_labels.ENTER, "Return")
        self.assertEqual(key_labels.MOD, "⌘")

    def test_get_keyboard_key_labels_for_windows(self):
        """
        Test the keyboard key labels with a Windows user agent.
        """
        self.client.defaults["HTTP_USER_AGENT"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        )
        response = self.client.get(reverse("wagtailadmin_home"))

        key_labels = get_keyboard_key_labels_from_request(response.wsgi_request)

        self.assertEqual(key_labels.ALT, "Alt")
        self.assertEqual(key_labels.CMD, "Ctrl")
        self.assertEqual(key_labels.CTRL, "Ctrl")
        self.assertEqual(key_labels.MOD, "Ctrl")


class TestKeyboardShortcutsDialog(WagtailTestUtils, TestCase):
    def setUp(self):
        self.test_user = self.create_test_user()
        self.login(user=self.test_user)

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
                    "data-controller": "w-kbd w-action",
                    "data-w-kbd-key-value": "?",
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

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=True)
    def test_keyboard_shortcuts_with_comments_enabled(self):
        """
        Test the presence of a comments shortcut if Comments enabled
        """
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/keyboard_shortcuts_dialog.html"
        )

        soup = self.get_soup(response.content)

        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        all_shortcuts_text = [
            kbd.string.strip() for kbd in shortcuts_dialog.select("kbd")
        ]

        self.assertIn("Add or show comments", shortcuts_dialog.prettify())
        self.assertIn("Ctrl + Alt + m", all_shortcuts_text)

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=False)
    def test_keyboard_shortcuts_with_comments_disabled(self):
        """
        Test the absence of a comments shortcut if Comments disabled
        """
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/keyboard_shortcuts_dialog.html"
        )

        soup = self.get_soup(response.content)

        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        all_shortcuts_text = [
            kbd.string.strip() for kbd in shortcuts_dialog.select("kbd")
        ]

        self.assertNotIn("comments", shortcuts_dialog.prettify())
        self.assertNotIn("Ctrl + Alt + m", all_shortcuts_text)

    def test_account_link_in_modal(self):
        """
        Test that the 'account' link fragment is correctly rendered in the
        keyboard shortcuts modal.
        """
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)

        soup = self.get_soup(response.content)
        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        self.assertIsNotNone(shortcuts_dialog)

        account_link = shortcuts_dialog.select_one("a[href$='account/']")
        self.assertIsNotNone(account_link)
        self.assertEqual(account_link.text.strip(), "account")
        self.assertIn("w-underline", account_link.get("class", []))

    def test_modal_shows_disabled_info_when_keyboard_shortcuts_disabled(self):
        """
        Modal should open and show warning if keyboard shortcuts are disabled.
        """
        profile = UserProfile.get_for_user(self.test_user)
        profile.keyboard_shortcuts = False
        profile.save()

        response = self.client.get(reverse("wagtailadmin_home"))

        soup = self.get_soup(response.content)
        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        self.assertIn(
            "Keyboard shortcuts are currently disabled", shortcuts_dialog.prettify()
        )

    def test_modal_shows_enabled_info_when_shortcuts_enabled(self):
        """
        Modal should show normal info when keyboard shortcuts are enabled.
        """
        profile = UserProfile.get_for_user(self.test_user)
        response = self.client.get(reverse("wagtailadmin_home"))
        soup = self.get_soup(response.content)
        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")

        self.assertTrue(profile.keyboard_shortcuts)
        self.assertIn(
            "Keyboard shortcuts are currently enabled", shortcuts_dialog.prettify()
        )


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
        self.assertIn("⌘", shortcuts_dialog.prettify())

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=True)
    def test_keyboard_shortcuts_with_comments_enabled(self):
        """
        Test the presence comments shortcut if Comments enabled
        """
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/keyboard_shortcuts_dialog.html"
        )

        soup = self.get_soup(response.content)

        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        all_shortcuts_text = [
            kbd.string.strip() for kbd in shortcuts_dialog.select("kbd")
        ]

        self.assertIn("Add or show comments", shortcuts_dialog.prettify())
        self.assertIn("^ + ⌥ + m", all_shortcuts_text)

    @override_settings(WAGTAILADMIN_COMMENTS_ENABLED=False)
    def test_keyboard_shortcuts_with_comments_disabled(self):
        """
        Test the absence comments shortcut if Comments disabled
        """
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "wagtailadmin/shared/keyboard_shortcuts_dialog.html"
        )

        soup = self.get_soup(response.content)

        shortcuts_dialog = soup.select_one("#keyboard-shortcuts-dialog")
        all_shortcuts_text = [
            kbd.string.strip() for kbd in shortcuts_dialog.select("kbd")
        ]

        self.assertNotIn("comments", shortcuts_dialog.prettify())
        self.assertNotIn("^ + ⌥ + m", all_shortcuts_text)
