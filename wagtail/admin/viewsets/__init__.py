from django.urls import include, re_path

from wagtail import hooks


class ViewSetRegistry:
    def __init__(self):
        self.viewsets = []

    def populate(self):
        for fn in hooks.get_hooks("register_admin_viewset"):
            viewset = fn()
            if isinstance(viewset, (list, tuple)):
                for vs in viewset:
                    self.register(vs)
            else:
                self.register(viewset)

    def register(self, viewset):
        self.viewsets.append(viewset)
        viewset.on_register()
        return viewset

    def get_urlpatterns(self):
        urlpatterns = []

        for viewset in self.viewsets:
            vs_urlpatterns = viewset.get_urlpatterns()

            if vs_urlpatterns:
                urlpatterns.append(
                    re_path(
                        r"^{}/".format(viewset.url_prefix),
                        include((vs_urlpatterns, viewset.name), namespace=viewset.name),
                    )
                )

        return urlpatterns


viewsets = ViewSetRegistry()
