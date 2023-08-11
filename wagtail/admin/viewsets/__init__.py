from django.urls import include, path

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
                    path(
                        f"{viewset.url_prefix}/",
                        include(
                            (vs_urlpatterns, viewset.url_namespace),
                            namespace=viewset.url_namespace,
                        ),
                    )
                )

        return urlpatterns


viewsets = ViewSetRegistry()
