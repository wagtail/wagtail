import jinja2
import jinja2.nodes

from jinja2.ext import Extension

from .templatetags.wagtailcore_tags import pageurl, richtext, slugurl, wagtail_version


class WagtailCoreExtension(Extension):
    tags = {'include_block'}

    def __init__(self, environment):
        super().__init__(environment)

        self.environment.globals.update({
            'pageurl': jinja2.contextfunction(pageurl),
            'slugurl': jinja2.contextfunction(slugurl),
            'wagtail_version': wagtail_version,
        })
        self.environment.filters.update({
            'richtext': richtext,
        })

    def parse(self, parser):
        parse_method = getattr(self, 'parse_' + parser.stream.current.value)

        return parse_method(parser)

    def parse_include_block(self, parser):
        lineno = next(parser.stream).lineno

        args = [parser.parse_expression()]

        with_context = True
        if parser.stream.current.test_any('name:with', 'name:without') and parser.stream.look().test('name:context'):
            with_context = next(parser.stream).value == 'with'
            parser.stream.skip()

        if with_context:
            args.append(jinja2.nodes.ContextReference())
        else:
            # Actually we can just skip else branch because context arg default to None
            args.append(jinja2.nodes.Const(None))

        node = self.call_method('_include_block', args, lineno=lineno)
        return jinja2.nodes.Output([node], lineno=lineno)

    def _include_block(self, value, context=None):
        if hasattr(value, 'render_as_block'):
            if context:
                new_context = context.get_all()
            else:
                new_context = {}

            return jinja2.Markup(value.render_as_block(context=new_context))

        return jinja2.Markup(value)


# Nicer import names
core = WagtailCoreExtension
