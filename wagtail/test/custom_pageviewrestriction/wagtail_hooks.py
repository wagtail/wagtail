from django.http.response import HttpResponseForbidden
from django.utils.cache import add_never_cache_headers

from wagtail import hooks
from wagtail.models.view_restrictions import get_page_view_restriction_model
from wagtail.wagtail_hooks import require_wagtail_login

PageViewRestriction = get_page_view_restriction_model()


@hooks.register("on_serve_page")
def check_custom_view_restrictions(callback):
    def check(page, request, serve_args, serve_kwargs):
        """
        Check whether there are any cutom view restrictions on this page which are
        not fulfilled by the given request object. If there are, return an
        HttpResponse that will notify the user of that restriction. If there are
        no such restrictions, return None.
        Note: Default page view restrictions are handled by Wagtail.
        """
        restrictions = page.get_view_restrictions().filter(
            restriction_type=PageViewRestriction.ADMIN
        )
        response = None
        for restriction in restrictions:
            if not restriction.accept_request(request):
                if not request.user.is_authenticated:
                    response = require_wagtail_login(next=request.get_full_path())
                    add_never_cache_headers(response)
                    return response

                response = HttpResponseForbidden()
                add_never_cache_headers(response)
                return response

        response = callback(page, request, serve_args, serve_kwargs)
        if restrictions:
            add_never_cache_headers(response)
        return response

    return check
