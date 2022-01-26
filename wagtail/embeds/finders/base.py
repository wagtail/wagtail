
class EmbedFinder:
    def accept(self, url):
        return False

    def find_embed(self, url, max_width=None, max_height=None):
        raise NotImplementedError
