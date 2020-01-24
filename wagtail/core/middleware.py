import warnings

from django.utils.deprecation import MiddlewareMixin
from wagtail.core.models import Site
from wagtail.utils.deprecation import RemovedInWagtail211Warning


class SiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request,
        according to hostname matching rules
        """
        warnings.warn(
            'Wagtail SiteMiddleware and the use of request.site is deprecated '
            'and will be removed in Wagtail 2.11. Update your middleware settings.',
            RemovedInWagtail211Warning, stacklevel=2
        )

        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None
