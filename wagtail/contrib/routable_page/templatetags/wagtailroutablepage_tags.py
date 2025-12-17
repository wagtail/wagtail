from django import template

from wagtail.models import Site

register = template.Library()


@register.simple_tag(takes_context=True)
def routablepageurl(context, page, url_name, *args, **kwargs):
    """
    ``routablepageurl`` is similar to ``pageurl``, but works with
    pages using ``RoutablePageMixin``. It behaves like a hybrid between the built-in
    ``reverse``, and ``pageurl`` from Wagtail.

    ``page`` is the RoutablePage that URLs will be generated from.

    ``url_name`` is a URL name defined in ``page.subpage_urls``.

    Positional arguments and keyword arguments should be passed as normal
    positional arguments and keyword arguments.
    """
    request = context["request"]
    site = Site.find_for_request(request)
    base_url = page.relative_url(site, request)
    routed_url = page.reverse_subpage(url_name, args=args, kwargs=kwargs)
    if not base_url.endswith("/"):
        base_url += "/"
    return base_url + routed_url


@register.simple_tag(takes_context=True)
def routablefullpageurl(context, page, url_name, *args, **kwargs):
    """
    ``routablefullpageurl`` is similar to ``routablepageurl``, but returns
    the full absolute URL (including protocol and domain).
    """
    request = context.get("request")
    base_url = page.get_full_url(request=request)

    if not base_url:
        return ""

    routed_url = page.reverse_subpage(url_name, args=args, kwargs=kwargs)

    if not base_url.endswith("/"):
        base_url += "/"
    if routed_url.startswith("/"):
        routed_url = routed_url[1:]

    return base_url + routed_url
