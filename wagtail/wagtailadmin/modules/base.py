from functools import wraps

from django.template.response import TemplateResponse

from wagtail.utils.urlpatterns import decorate_urlpatterns


class Module(object):
    app_name = ''

    def __init__(self, namespace, **kwargs):
        self.namespace = namespace

        for key, value in kwargs.items():
            setattr(self, key, value)

    def has_module_permission(self, request):
        return True

    def get_urls(self):
        return ()

    def process_request(self, request):
        # Add link to module to request object
        request.module = self

        # Add current_app to request object
        request.current_app = self.namespace

    def _wrap_view(self, view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            self.process_request(request)

            return view(request, *args, **kwargs)

        return wrapper

    def _get_wrapped_urls(self):
        urls = self.get_urls()
        return decorate_urlpatterns(urls, self._wrap_view)

    @property
    def urls(self):
        return self._get_wrapped_urls(), self.namespace, self.app_name


# module_view decorator for function-based views
def module_view(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        return view(request.module, request, *args, **kwargs)

    return wrapper
