import re

from django.test import TestCase
from django.urls import reverse

from wagtail.admin.urls import get_sprite_hash, sprite_hash


class TestIconSprite(TestCase):
    def test_get_sprite_hash(self):
        result = get_sprite_hash()
        self.assertTrue(bool(re.match(r"^[a-z0-9]{8}$", result)))

    def test_hash_var(self):
        self.assertTrue(isinstance(sprite_hash, str))
        self.assertTrue(len(sprite_hash) == 8)

    def test_url(self):
        url = reverse("wagtailadmin_sprite")
        self.assertEqual(url[:14], "/admin/sprite-")

    def test_view(self):
        response = self.client.get(reverse("wagtailadmin_sprite"))
        self.assertTrue("Content-Type: text/html; charset=utf-8" in str(response.serialize_headers()))
