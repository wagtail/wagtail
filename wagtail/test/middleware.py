from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

from wagtail.models import Page
from wagtail.views import serve


class BlockDodgyUserAgentMiddleware(MiddlewareMixin):
    # Used to test that we're correctly handling responses returned from middleware during page
    # previews. If a client with user agent "EvilHacker" calls an admin view that performs a
    # preview, the request to /admin/... will pass this middleware, but the fake request used for
    # the preview (which keeps the user agent header, but uses the URL path of the front-end page)
    # will trigger a Forbidden response. In this case, the expected behaviour is to return that
    # response back to the user.

    def process_request(self, request):
        if (
            not request.path.startswith("/admin/")
            and request.headers.get("user-agent") == "EvilHacker"
        ):
            return HttpResponseForbidden("Forbidden")


class SimplePageViewInterceptorMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if serve == view_func:
            page = Page.find_for_request(request, *view_args, **view_kwargs)
            if page is None:
                raise Http404
            elif page.content == "Intercept me":
                return HttpResponse("Intercepted")
