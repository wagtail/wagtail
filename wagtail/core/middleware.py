import warnings

from django.utils.deprecation import MiddlewareMixin
from wagtail.core.models import Site
from wagtail.utils.deprecation import RemovedInWagtail28Warning


class SiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request,
        according to hostname matching rules
        """
        warnings.warn(
            'wagtail SiteMiddleware and the use of request.site is deprecated '
            'and will be removed in wagtail 2.8. Update your middleware settings.',
            RemovedInWagtail28Warning, stacklevel=2
        )

        try:
            request._wagtail_site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request._wagtail_site = None
