"""DeferredError class taken from PIL._util.py file."""


class DeferredError:  # pylint: disable=too-few-public-methods
    """Allows failing import for doc purposes, as C module will be not build during docs build."""

    def __init__(self, ex):
        self.ex = ex

    def __getattr__(self, elt):
        raise self.ex
