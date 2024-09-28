from .base import BaseBackend


class DummyBackend(BaseBackend):
    def __init__(self):
        super().__init__()

        self.urls = []

    def purge(self, url) -> None:
        self.urls.append(url)
