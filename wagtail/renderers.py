import functools

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.module_loading import import_string
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework.utils.mediatypes import (
    _MediaType,
    media_type_matches,
    order_by_precedence,
)


class BasePageRenderer:
    media_type = None

    def render(self, request, media_type, page, args, kwargs):
        raise NotImplementedError("Renderer class requires .render() to be implemented")


class ServePageRenderer(BasePageRenderer):
    """
    Renders a page by calling the .serve() method on the model.
    """

    media_type = "text/html"

    def render(self, request, media_type, page, args, kwargs):
        return page.serve(request, *args, **kwargs)


@functools.lru_cache()
def get_page_renderers():
    """
    Returns the list of renderer classes that are registered in WAGTAIL_PAGE_RENDERERS.
    """
    renderer_strings = getattr(
        settings, "WAGTAIL_PAGE_RENDERERS", ["wagtail.renderers.ServePageRenderer"]
    )

    return [import_string(renderer_string)() for renderer_string in renderer_strings]


@receiver(setting_changed)
def reset_page_renderers_cache(**kwargs):
    """
    Clear cache when WAGTAIL_PAGE_RENDERERS setting is changed
    """
    if kwargs["setting"] in ("WAGTAIL_PAGE_RENDERERS"):
        get_page_renderers.cache_clear()


class PageRendererNotFoundError(LookupError):
    pass


def get_page_renderer_for_request(request):
    """
    Returns the best renderer to use for the request.

    If no renderer can be found for the requests, this raises RendererNotFoundError

    Args:
        request (Request): A Django Request object to find a renderer for

    Raises:
        PageRendererNotFoundError: If there is no renderer that could be used for the request
    """
    # Implementation is based on similar code in Django REST Framework
    # https://github.com/encode/django-rest-framework/blob/71e6c30034a1dd35a39ca74f86c371713e762c79/rest_framework/negotiation.py
    header = request.META.get("HTTP_ACCEPT", "*/*")
    accept_list = [token.strip() for token in header.split(",")]

    for media_type_set in order_by_precedence(accept_list):
        for renderer in get_page_renderers():
            for media_type in media_type_set:
                if media_type_matches(renderer.media_type, media_type):
                    # Return the most specific media type as accepted.
                    media_type_wrapper = _MediaType(media_type)
                    if (
                        _MediaType(renderer.media_type).precedence
                        > media_type_wrapper.precedence
                    ):
                        # Eg client requests '*/*'
                        # Accepted media type is 'application/html'
                        full_media_type = ";".join(
                            (renderer.media_type,)
                            + tuple(
                                "{}={}".format(key, value.decode(HTTP_HEADER_ENCODING))
                                for key, value in media_type_wrapper.params.items()
                            )
                        )
                        return renderer, full_media_type
                    else:
                        # Eg client requests 'application/json; indent=8'
                        # Accepted media type is 'application/json; indent=8'
                        return renderer, media_type

    raise PageRendererNotFoundError(
        f"Could not find a renderer for media type '{media_type}'"
    )
