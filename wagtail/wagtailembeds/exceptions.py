from __future__ import absolute_import, unicode_literals


class EmbedException(Exception):
    pass


class EmbedUnsupportedProviderException(EmbedException):
    pass


class EmbedNotFoundException(EmbedException):
    pass
