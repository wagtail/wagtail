(varying_page_responses)=

# How to vary page responses

A page can return different responses at the same URL depending on the request, for example HTML for browsers and Markdown for clients that ask for it. When it does, the response must say which request headers it depends on, using the `Vary` header. Without it, a cache can store one version of the page and serve it to every client.

Wagtail chooses between the formats a page offers, and adds the `Vary` header for you. You decide how each format is rendered, and how your cache is configured.

## Serving more than one format

List the formats a page type can respond with in {attr}`~wagtail.models.AbstractPage.response_media_types`, then use {meth}`~wagtail.models.AbstractPage.get_response_media_type` in {meth}`~wagtail.models.AbstractPage.serve` to pick the response:

```python
from django.template.response import TemplateResponse

from wagtail.models import Page


class BlogPage(Page):
    response_media_types = ["text/html", "text/markdown"]

    def serve(self, request, *args, **kwargs):
        if self.get_response_media_type(request) == "text/markdown":
            return TemplateResponse(
                request,
                "blog/blog_page.md",
                self.get_context(request, *args, **kwargs),
                content_type="text/markdown; charset=utf-8",
            )
        return super().serve(request, *args, **kwargs)
```

Django templates, and Jinja2 templates rendered through Django, escape their output for HTML whatever the file extension. Turn this off in Markdown templates with `{% autoescape off %}` in Django templates, or `{% autoescape false %}` in Jinja2.

`get_response_media_type()` compares the request's `Accept` header with `response_media_types`:

-   The first item is the default. It is used when the client has no preference between the available types, as with `Accept: */*`, `Accept: text/*`, a typical browser `Accept` header, or no `Accept` header at all.
-   A client that prefers another item gets it: `Accept: text/markdown` returns `"text/markdown"`.
-   When the client accepts none of the available types, the default is used rather than returning an error.

Wagtail adds `Vary: Accept` to every response from a page with more than one item in `response_media_types`, including its HTML responses. Pages with a single media type, which is the default, are not affected.

Other parts of your site can add to the `Vary` header too. For example, Django adds `Vary: Cookie` when a template uses the session, which the Wagtail user bar does. If that happens in your HTML template but not your Markdown one, the two formats vary on different headers, which is unsafe with some caches. See [](varying_page_responses_caching).

## Varying on other request headers

Wagtail adds the headers returned by {meth}`~wagtail.models.AbstractPage.get_vary_headers` to the `Vary` header of the page's responses. By default, this includes `Accept` for pages with more than one media type.

If your page changes its response based on anything else in the request, override `get_vary_headers()` to include it:

```python
class MemberPage(Page):
    def get_vary_headers(self, request):
        return [*super().get_vary_headers(request), "Cookie"]
```

## Routable pages

On a page using [`RoutablePageMixin`](routable_page_mixin), choose the format inside each route that offers more than one, the same way as in `serve()` above. `Vary: Accept` is added to the responses of all routes. To leave it out for routes that only respond with one format, check the name of the matched route:

```python
class BlogIndexPage(RoutablePageMixin, Page):
    response_media_types = ["text/html", "text/markdown"]

    def get_vary_headers(self, request):
        headers = super().get_vary_headers(request)
        # Only set when the page is served through Wagtail's routing
        match = getattr(request, "routable_resolver_match", None)
        if match and match.url_name != "index_route":
            headers.remove("Accept")
        return headers
```

## Responses that Wagtail doesn't add the headers to

Wagtail adds the `Vary` header in the view that serves pages, after `serve()` and any [`on_serve_page`](on_serve_page) hooks have run. It doesn't add it to:

-   Responses returned by [`before_serve_page`](before_serve_page) hooks. The password prompt and the login redirect for private pages are returned by an `on_serve_page` hook, so they do get the headers.
-   Previews in the admin.
-   Your own views that call `page.serve()` directly. Use Django's {func}`~django.utils.cache.patch_vary_headers` there.
-   Error pages, such as the 404 page, which are rendered by Django's error handlers rather than by a page. See [](varying_error_pages).

(varying_error_pages)=

## Error pages

To return a 404 page in other formats too, set a custom {data}`~django.conf.urls.handler404` view that makes the same choice, with {meth}`request.get_preferred_type() <django.http.HttpRequest.get_preferred_type>`:

```python
# myproject/views.py
from django.http import HttpResponseNotFound
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from django.views.defaults import page_not_found as default_page_not_found


def page_not_found(request, exception):
    if request.get_preferred_type(["text/html", "text/markdown"]) == "text/markdown":
        response = HttpResponseNotFound(
            render_to_string("404.md", request=request),
            content_type="text/markdown; charset=utf-8",
        )
    else:
        response = default_page_not_found(request, exception)
    patch_vary_headers(response, ["Accept"])
    return response
```

```python
# myproject/urls.py
handler404 = "myproject.views.page_not_found"
```

Django only uses `handler404` when `DEBUG` is `False`.

(varying_page_responses_caching)=

## Caching

The `Vary` header only protects your pages if the caches in front of them take it into account. Some CDNs can ignore `Vary: Accept` by default, so check how yours handles it. If it doesn't use the header, either configure the CDN to include the `Accept` header in its cache key, or keep the other formats out of shared caches with {func}`~django.utils.cache.patch_cache_control`, for example `patch_cache_control(response, private=True)`.

If you use Django's cache middleware, make every variant of a page vary on the same headers. The middleware stores a single list of headers for each URL, and replaces it with the list from each response it caches. If only one variant varies on a header, for example because only the HTML template accesses the session and adds `Vary: Cookie`, the cache stops checking that header after caching another variant. A page cached for an anonymous visitor can then be served to a logged-in user. To avoid this, add the header in `get_vary_headers()`.
