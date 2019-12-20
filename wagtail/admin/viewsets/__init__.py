from django.conf.urls import url, include

from wagtail.core import hooks


class ViewSetRegistry:
    def __init__(self):
        self.viewsets = []

    def populate(self):
        for fn in hooks.get_hooks('register_admin_viewset'):
            viewset = fn()
            self.register(viewset)

    def register(self, viewset_cls):
        self.viewsets.append(viewset_cls)
        return viewset_cls

    def get_urlpatterns(self):
        urlpatterns = []

        for viewset in self.viewsets:
            vs_urlpatterns = viewset.get_urlpatterns()

            if vs_urlpatterns:
                urlpatterns.append(url(
                    r'^{}/'.format(viewset.url_prefix),
                    include((vs_urlpatterns, viewset.name), namespace=viewset.name)
                ))

        return urlpatterns


viewsets = ViewSetRegistry()
