from .base import BaseBackend


class DummyBackend(BaseBackend):
    # Backends are instantiated on each purge, so store URLs on the class
    urls = []

    def purge(self, url) -> None:
        DummyBackend.urls.append(url)

    @classmethod
    def reset(cls) -> None:
        DummyBackend.urls.clear()
