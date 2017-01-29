from __future__ import absolute_import, unicode_literals

import django
from django.utils.translation import activate
from wagtail.wagtailcore.models import Site


if django.VERSION >= (1, 10):
    from django.utils.deprecation import MiddlewareMixin
else:
    MiddlewareMixin = object



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


class LocaleAdminMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Set the user prefered language in wagtail admin urls
        :param request:
        :return:
        """
        if 'admin' in request.path:  # TODO: Change to a proper way to look if is admin
            if request.user:
                activate(request.user.wagtail_userprofile.prefered_language)
