import jinja2
import jinja2.nodes
from jinja2.ext import Extension
from markupsafe import Markup, escape

from .templatetags.wagtailcore_tags import (
    fullpageurl,
    pageurl,
    richtext,
    slugurl,
    wagtail_site,
    wagtail_version,
)


class WagtailCoreExtension(Extension):
    tags = {"include_block"}

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


# Nicer import names
core = WagtailCoreExtension
