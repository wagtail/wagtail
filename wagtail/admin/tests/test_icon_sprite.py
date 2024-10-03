from django.test import SimpleTestCase

from wagtail.admin.icons import get_icon_sprite_hash, get_icon_sprite_url


class TestIconSpriteView(SimpleTestCase):
    def test_content_type(self):
        response = self.client.get(get_icon_sprite_url())
        self.assertEqual(
            response.headers["Content-Type"], "image/svg+xml; charset=utf-8"
        )
        self.assertEqual(response.wsgi_request.GET["h"], get_icon_sprite_hash())

    def test_no_comments(self):
        response = self.client.get(get_icon_sprite_url())
        self.assertNotContains(response, "<!--")


class TestIconSpriteHash(SimpleTestCase):
    def test_hash(self):
        self.assertEqual(len(get_icon_sprite_hash()), 8)
