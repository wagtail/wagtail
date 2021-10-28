from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


class BlockDodgyUserAgentMiddleware(MiddlewareMixin):
    # Used to test that we're correctly handling responses returned from middleware during page
    # previews. If a client with user agent "EvilHacker" calls an admin view that performs a
    # preview, the request to /admin/... will pass this middleware, but the fake request used for
    # the preview (which keeps the user agent header, but uses the URL path of the front-end page)
    # will trigger a Forbidden response. In this case, the expected behaviour is to return that
    # response back to the user.

    def process_request(self, request):
        if not request.path.startswith('/admin/') and request.META.get('HTTP_USER_AGENT') == 'EvilHacker':
            return HttpResponseForbidden("Forbidden")
