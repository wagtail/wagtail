from django.conf.urls import url, include

from wagtail.wagtailcore import hooks


def register_viewsets():
    for fn in hooks.get_hooks('register_admin_viewset'):
        viewset = fn()

        if viewset:
            urlpatterns = viewset.get_urlpatterns()

            if urlpatterns:
                @hooks.register('register_admin_urls')
                def register_admin_urls():
                    return [
                        url(
                            r'^{}/'.format(viewset.name),
                            include(urlpatterns, app_name=viewset.name, namespace=viewset.name)
                        ),
                    ]
