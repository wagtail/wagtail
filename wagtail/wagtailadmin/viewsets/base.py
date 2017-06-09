from __future__ import absolute_import, unicode_literals


class ViewSet(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.url_prefix = kwargs.pop('url_prefix', self.name)

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_urlpatterns(self):
        return []
