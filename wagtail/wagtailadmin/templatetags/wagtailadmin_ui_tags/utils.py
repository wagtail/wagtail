from __future__ import unicode_literals
from inspect import getargspec

from django.template import Node, TemplateSyntaxError
from django.template.base import parse_bits, TextNode
from django.template.loader_tags import BlockNode


class WuiNode(Node):

    def __init__(self, inner, args, kwargs):
        self.args = args
        self.kwargs = kwargs
        self.inner = inner

    def render(self, context):
        args = [var.resolve(context) for var in self.args]
        kwargs = {name: var.resolve(context)
                  for name, var in self.kwargs.items()}

        return self.render_template(context, *args, **kwargs)

    @classmethod
    def handle(cls, parser, token):
        name = cls.TAG_NAME

        bits = token.split_contents()[1:]
        # This is typically taken from getargspec, but we are doing funky things...

        args, varargs, varkw, defaults = getargspec(cls.render_template)
        args = args[2:]  # ignore self and inner arguments

        args, kwargs = parse_bits(
            parser, bits, args, varargs, varkw, defaults,
            takes_context=False, name=name)

        # Get the contents till {% endbutton %}
        inner = parser.parse(['end' + name])
        parser.delete_first_token()
        inner = cls.parse_inner(inner)

        return cls(inner, args, kwargs)

    @classmethod
    def parse_inner(cls, inner):
        return inner


class WuiOptionalBlockNode(WuiNode):

    def render_blocks(self, context):
        return {key: nodelist.render(context)
                for key, nodelist in self.inner.items()}

    @classmethod
    def parse_inner(cls, nodelist):
        name = 'block'
        end_tag = 'end' + name

        blocks = cls.OPTIONAL_BLOCKS

        final_nodelists = {}

        for node in nodelist:
            if isinstance(node, TextNode):
                if not node.s.isspace():
                    raise TemplateSyntaxError('Illegal content inside "%s" template tag' % cls.TAG_NAME)
            elif not isinstance(node, BlockNode):
                raise TemplateSyntaxError('Illegal template tag inside "%s" template tag' % cls.TAG_NAME)
            elif node.name not in blocks:
                raise TemplateSyntaxError('Non-whitelisted block name inside "%s" template tag' % cls.TAG_NAME)
            else:
                final_nodelists[node.name] = node.nodelist

        return final_nodelists
