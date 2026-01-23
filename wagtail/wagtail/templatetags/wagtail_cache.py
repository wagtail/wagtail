from django import template
from django.template import Variable
from django.template.exceptions import TemplateSyntaxError
from django.templatetags.cache import CacheNode as DjangoCacheNode

from wagtail.models import PAGE_TEMPLATE_VAR, Site

register = template.Library()


class WagtailCacheNode(DjangoCacheNode):
    """
    A modified version of Django's `CacheNode` which is aware of Wagtail's
    page previews.
    """

    def render(self, context):
        try:
            request = context["request"]
        except KeyError:
            # When there's no request, it's not possible to tell whether this is a preview or not.
            # Bypass the cache to be safe.
            return self.nodelist.render(context)

        if getattr(request, "is_preview", False):
            # Skip cache in preview
            return self.nodelist.render(context)

        return super().render(context)


class WagtailPageCacheNode(WagtailCacheNode):
    """
    A modified version of Django's `CacheNode` designed for caching fragments
    of pages.

    This tag intentionally makes assumptions about what context is available.
    If these assumptions aren't valid, it's recommended to just use `{% wagtailcache %}`.
    """

    CACHE_SITE_TEMPLATE_VAR = "wagtail_page_cache_site"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pretend the user specified the page and site as part of context
        self.vary_on.extend(
            [
                Variable(f"{PAGE_TEMPLATE_VAR}.cache_key"),
                Variable(f"{self.CACHE_SITE_TEMPLATE_VAR}.pk"),
            ]
        )

    def render(self, context):
        if "request" in context:
            # Inject the site into context to be picked up when resolving `vary_on`
            with context.update(
                {
                    self.CACHE_SITE_TEMPLATE_VAR: Site.find_for_request(
                        context["request"]
                    )
                }
            ):
                return super().render(context)
        return super().render(context)


def register_cache_tag(tag_name, node_class):
    """
    A helper function to define cache tags without duplicating `do_cache`.
    """

    @register.tag(tag_name)
    def do_cache(parser, token):
        # Implementation copied from `django.templatetags.cache.do_cache`
        nodelist = parser.parse((f"end{tag_name}",))
        parser.delete_first_token()
        tokens = token.split_contents()
        if len(tokens) < 3:
            raise TemplateSyntaxError(
                f"'{tokens[0]}' tag requires at least 2 arguments."
            )
        if len(tokens) > 3 and tokens[-1].startswith("using="):
            cache_name = parser.compile_filter(tokens[-1][len("using=") :])
            tokens = tokens[:-1]
        else:
            cache_name = None
        return node_class(
            nodelist,
            parser.compile_filter(tokens[1]),
            tokens[2],  # fragment_name can't be a variable.
            [parser.compile_filter(t) for t in tokens[3:]],
            cache_name,
        )


register_cache_tag("wagtailcache", WagtailCacheNode)
register_cache_tag("wagtailpagecache", WagtailPageCacheNode)
