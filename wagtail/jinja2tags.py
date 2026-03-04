import jinja2
import jinja2.nodes
from django.core.cache import InvalidCacheBackendError, caches
from django.core.cache.utils import make_template_fragment_key
from jinja2.ext import Extension
from markupsafe import Markup, escape

from wagtail.coreutils import make_wagtail_template_fragment_key
from wagtail.models import PAGE_TEMPLATE_VAR, Site

from .templatetags.wagtailcore_tags import (
    fullpageurl,
    pageurl,
    richtext,
    slugurl,
    wagtail_site,
    wagtail_version,
)


class WagtailCoreExtension(Extension):
    tags = {"include_block", "wagtailcache", "wagtailpagecache"}

    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update(
            {
                "fullpageurl": jinja2.pass_context(fullpageurl),
                "pageurl": jinja2.pass_context(pageurl),
                "slugurl": jinja2.pass_context(slugurl),
                "wagtail_site": jinja2.pass_context(wagtail_site),
                "wagtail_version": wagtail_version,
            }
        )
        self.environment.filters.update(
            {
                "richtext": richtext,
            }
        )

    def parse(self, parser):
        parse_method = getattr(self, "parse_" + parser.stream.current.value)

        return parse_method(parser)

    def parse_include_block(self, parser):
        lineno = next(parser.stream).lineno

        args = [parser.parse_expression()]

        # always pass context to _include_block - even if we're not passing it on to render_as_block,
        # we need it to see if autoescaping is enabled
        if hasattr(jinja2.nodes, "DerivedContextReference"):
            # DerivedContextReference includes local variables. Introduced in Jinja 2.11
            args.append(jinja2.nodes.DerivedContextReference())
        else:
            args.append(jinja2.nodes.ContextReference())

        use_context = True
        if parser.stream.current.test_any(
            "name:with", "name:without"
        ) and parser.stream.look().test("name:context"):
            use_context = next(parser.stream).value == "with"
            parser.stream.skip()

        args.append(jinja2.nodes.Const(use_context))

        node = self.call_method("_include_block", args, lineno=lineno)
        return jinja2.nodes.Output([node], lineno=lineno)

    def _include_block(self, value, context, use_context):
        if hasattr(value, "render_as_block"):
            if use_context:
                new_context = context.get_all()
            else:
                new_context = {}

            result = value.render_as_block(context=new_context)
        else:
            result = value

        if context.eval_ctx.autoescape:
            return escape(result)
        else:
            return Markup(result)

    def parse_wagtailpagecache(self, parser):
        return self._parse_wagtail_cache_tag(parser)

    def parse_wagtailcache(self, parser):
        return self._parse_wagtail_cache_tag(parser)

    def _parse_wagtail_cache_tag(self, parser):
        tag_name = next(parser.stream).value
        lineno = parser.stream.current.lineno

        expire_time = parser.parse_expression()
        fragment_name = parser.parse_expression()

        vary_on = []
        while not parser.stream.current.test("block_end"):
            vary_on.append(parser.parse_expression())

        body = parser.parse_statements((f"name:end{tag_name}",), drop_needle=True)

        return jinja2.nodes.CallBlock(
            self.call_method(
                "_cached_render",
                [
                    jinja2.nodes.Const(tag_name),
                    jinja2.nodes.DerivedContextReference(),
                    expire_time,
                    fragment_name,
                    jinja2.nodes.List(vary_on),
                ],
            ),
            [],
            [],
            body,
        ).set_lineno(lineno)

    def _cached_render(
        self, tag_name, context, expire_time, fragment_name, vary_on, caller
    ):
        request = context.get("request")

        if request is None or getattr(request, "is_preview", False):
            # Skip the cache in preview
            return caller()

        try:
            fragment_cache = caches["template_fragments"]
        except InvalidCacheBackendError:
            fragment_cache = caches["default"]

        if tag_name == "wagtailcache":
            cache_key = make_template_fragment_key(fragment_name, vary_on)
        else:
            page = context.get(PAGE_TEMPLATE_VAR, None)
            site = Site.find_for_request(request)
            cache_key = make_wagtail_template_fragment_key(
                fragment_name, page, site, vary_on
            )

        if (value := fragment_cache.get(cache_key)) is None:
            value = caller()
            fragment_cache.set(cache_key, value, expire_time)

        return value


# Nicer import names
core = WagtailCoreExtension
