import warnings

from django.utils.deprecation import MiddlewareMixin
from wagtail.core.models import Site
from wagtail.utils.deprecation import RemovedInWagtail211Warning


warnings.warn(
    'wagtail.core.middleware.SiteMiddleware and the use of request.site is deprecated. '
    'Please update your code to use Site.find_for_request(request) in place of request.site, '
    'and remove wagtail.core.middleware.SiteMiddleware from MIDDLEWARES',
    RemovedInWagtail211Warning
)


class SiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request,
        according to hostname matching rules
        """
        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None
