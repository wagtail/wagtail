from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


class BlockDodgyUserAgentMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.path.startswith('/admin/') and request.META.get('HTTP_USER_AGENT') == 'EvilHacker':
            return HttpResponseForbidden("Forbidden")
