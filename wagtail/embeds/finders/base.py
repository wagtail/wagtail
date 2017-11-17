from __future__ import absolute_import, unicode_literals


class EmbedFinder(object):
    def accept(self, url):
        return False

    def find_embed(self, url, max_width=None):
        raise NotImplementedError
