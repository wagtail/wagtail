from django.test import SimpleTestCase

from wagtail.admin.icons import get_icon_sprite_hash, get_icon_sprite_url, get_icons
from wagtail.test.utils.wagtail_tests import WagtailTestUtils


class TestIconSpriteView(WagtailTestUtils, SimpleTestCase):
    def test_content_type(self):
        response = self.client.get(get_icon_sprite_url())
        self.assertEqual(
            response.headers["Content-Type"], "image/svg+xml; charset=utf-8"
        )
        self.assertEqual(response.wsgi_request.GET["h"], get_icon_sprite_hash())

    def test_no_comments(self):
        response = self.client.get(get_icon_sprite_url())
        self.assertNotContains(response, "<!--")

    def test_register_icons_hook(self):
        get_icons.cache_clear()
        self.addCleanup(get_icons.cache_clear)

        def register_icons(icons):
            # The hook should receive the existing icons as an argument
            self.assertIn("wagtailadmin/icons/wagtail.svg", icons)
            return icons + [
                "tests/icons/single-quotes.svg",  # id='icon-single-quotes'
            ]

        with self.register_hook("register_icons", register_icons):
            response = self.client.get(get_icon_sprite_url())

        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        icon = soup.select_one("symbol#icon-single-quotes")
        self.assertIsNotNone(icon)


class TestIconSpriteHash(SimpleTestCase):
    def test_hash(self):
        self.assertEqual(len(get_icon_sprite_hash()), 8)
