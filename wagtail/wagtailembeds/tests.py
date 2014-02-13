from django.test import TestCasez

from .embeds import get_embed


class TestEmbeds(TestCase):
    # FIXME: test currently depends on a valid EMBEDLY_KEY being set - we don't particularly
    # want to put one in runtests.py. See https://github.com/torchbox/wagtail/issues/26 for
    # progress on eliminating Embedly as a dependency
    def DISABLEDtest_get_embed(self):
        # This test will fail if the video is removed or the title is changed
        embed = get_embed('http://www.youtube.com/watch?v=S3xAeTmsJfg')
        self.assertEqual(embed.title, 'Animation: Ferret dance (A series of tubes)')
