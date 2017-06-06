from __future__ import absolute_import, unicode_literals


class APIField(object):
    def __init__(self, name, serializer=None):
        self.name = name
        self.serializer = serializer

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '<APIField {}>'.format(self.name)
