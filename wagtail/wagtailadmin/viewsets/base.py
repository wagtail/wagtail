from __future__ import absolute_import, unicode_literals


class ViewSet(object):
    def __init__(self, name, **kwargs):
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_urlpatterns(self):
        return []
