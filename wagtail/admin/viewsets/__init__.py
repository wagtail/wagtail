from django.urls import include, path

from wagtail import hooks
from wagtail.admin.viewsets.base import ViewSetGroup


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
        # Allow registering a ViewSetGroup, which will register all of its
        # registerables.
        if isinstance(viewset, ViewSetGroup):
            for vs in viewset.registerables:
                self.register(vs)
            viewset.on_register()
            return

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
