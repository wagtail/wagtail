from inspect import getfullargspec, unwrap

from django.core.exceptions import ImproperlyConfigured
from django.template.library import InclusionNode, parse_bits


class PartialNode(InclusionNode):
    """
    Splits an existing template into to based on a string provided in the template
    to act as two separate virtual (partial) templates for a start & end either
    side of the split string.
    The split string is not included in either final template.
    """

    def __init__(self, *args, **kwargs):
        is_end = kwargs.pop("is_end", False)
        split_tag = kwargs.pop("split_tag")  # required

        super().__init__(*args, **kwargs)

        self.is_end = is_end
        self.split_tag = split_tag

    def render(self, context):
        template = context.template.engine.get_template(self.filename)
        source = template.source
        parts = source.split(self.split_tag)

        # patch in a template that is just a partial version of the original & re-apply metadata for debugging
        self.filename = context.template.engine.from_string(
            parts[1] if self.is_end else parts[0]
        )
        self.filename.name = template.name
        self.filename.origin = template.origin
        self.filename.source = template.source

        content = super().render(context)

        return content


class SplitTemplateTag:
    """
    Base class for building a split template tag in the format.
    `{% birdbath %} {% birdbathend %}`
    Must provide `name` (the template tag name) and `filename` (the template inclusion).
    `start` & `end` static methods can be overridden to be used as the template tag functions
    and will behave the same way as functions used with `@register.inclusion_tag`. By default these return an empty context Dict.
    `takes_context` will set the context as the first param of start and end function.
    """

    name = ""
    takes_context = False
    filename = ""
    split_tag = "<!-- START:END -->"

    def __init__(self, register):
        if not self.name:
            raise ImproperlyConfigured("`name` must be provided to the class.")

        if not self.filename:
            raise ImproperlyConfigured("`filename` must be provided to the class.")

        self.register = register

    @staticmethod
    def start():
        """Emulates what you would pass into register inclusion tag."""
        return {}

    @staticmethod
    def end():
        """Emulates what you would pass into register inclusion tag."""
        return {}

    def get_tag(self, is_end=False):
        takes_context = self.takes_context
        filename = self.filename
        split_tag = self.split_tag
        name = f"end{self.name}" if is_end else self.name
        func = self.end if is_end else self.start
        func.__name__ = name  # ensure the debugging name matches the template tag

        def tag(parser, token):
            (
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                _,
            ) = getfullargspec(unwrap(func))

            bits = token.split_contents()[1:]

            args, kwargs = parse_bits(
                parser,
                bits,
                params,
                varargs,
                varkw,
                defaults,
                kwonly,
                kwonly_defaults,
                takes_context,
                name,
            )

            return PartialNode(
                func,
                takes_context,
                args,
                kwargs,
                filename,
                split_tag=split_tag,
                is_end=is_end,
            )

        return [name, tag]

    def register_tags(self):
        self.register.tag(*self.get_tag())
        self.register.tag(*self.get_tag(is_end=True))
