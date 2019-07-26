from django.utils.deprecation import MiddlewareMixin

from wagtail.core.models import get_site_model


class SiteMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Set request.site to contain the Site object responsible for handling this request,
        according to hostname matching rules
        """
        Site = get_site_model()
        try:
            request.site = Site.find_for_request(request)
        except Site.DoesNotExist:
            request.site = None
