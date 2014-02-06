from django.test import TestCase

from .embeds import get_embed

class TestEmbeds(TestCase):
    def test_get_embed(self):
        # This test will fail if the video is removed or the title is changed
        embed = get_embed('http://www.youtube.com/watch?v=S3xAeTmsJfg')
        self.assertEqual(embed.title, 'Animation: Ferret dance (A series of tubes)')
