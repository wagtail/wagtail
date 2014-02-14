from django.test import TestCase
from unittest import skip
from wagtail.wagtailembeds import get_embed


class TestEmbeds(TestCase):
    def setUp(self):
        self.hit_count = 0

    def test_get_embed(self):
        embed = get_embed('www.test.com/1234', max_width=400, finder=self.dummy_finder)

        # Check that the embed is correct
        self.assertEqual(embed.title, "Test: www.test.com/1234")
        self.assertEqual(embed.type, 'video')
        self.assertEqual(embed.width, 400)

        # Check that there has only been one hit to the backend
        self.assertEqual(self.hit_count, 1)

        # Look for the same embed again and check the hit count hasn't increased
        embed = get_embed('www.test.com/1234', max_width=400, finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 1)

        # Look for a different embed, hit count should increase
        embed = get_embed('www.test.com/4321', max_width=400, finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 2)

        # Look for the same embed with a different width, this should also increase hit count
        embed = get_embed('www.test.com/4321', finder=self.dummy_finder)
        self.assertEqual(self.hit_count, 3)

    def dummy_finder(self, url, max_width=None):
        # Up hit count
        self.hit_count += 1

        # Return a pretend record
        return {
            'title': "Test: " + url,
            'type': 'video',
            'thumbnail_url': '',
            'width': max_width if max_width else 640,
            'height': 480,
            'html': "<p>Blah blah blah</p>",
        }