from django.conf.urls import url, include

from wagtail.wagtailcore import hooks


def register_modules():
    for fn in hooks.get_hooks('register_admin_module'):
        module = fn()

        if module:
            urlpatterns = module.get_urlpatterns()

            if urlpatterns:
                @hooks.register('register_admin_urls')
                def register_admin_urls():
                    return  [
                        url(
                            r'^{}/'.format(module.name),
                            include(urlpatterns, app_name=module.name, namespace=module.name)
                        ),
                    ]
