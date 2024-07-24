from html import escape
from typing import Sequence, Union

from draftjs_exporter.engines.base import Attr
from draftjs_exporter.engines.string import DOMString, Elt, VOID_ELEMENTS
from draftjs_exporter.types import HTML


class DOMStringCompat(DOMString):
    """
    The same as DOMString, but with as much backwards-compatibility as possible.
    """

    @staticmethod
    def render_attrs(attr: Attr) -> str:
        attrs = [f' {k}="{escape(v)}"' for k, v in attr.items()]
        # Compat: reverts "Remove HTML attributes alphabetical sorting of default string engine ([#129](https://github.com/springload/draftjs_exporter/pull/129))"
        attrs.sort()
        return "".join(attrs)

    @staticmethod
    def render_children(children: Sequence[Union[HTML, Elt]]) -> HTML:
        return "".join(
            [
                DOMStringCompat.render(c) if isinstance(c, Elt)
                # Compat: reverts "Disable single and double quotes escaping outside of attributes for string engine ([#129](https://github.com/springload/draftjs_exporter/pull/129))"
                else escape(c, quote=True)
                for c in children
            ]
        )

    @staticmethod
    def render(elt: Elt) -> HTML:
        type_ = elt.type
        attr = DOMStringCompat.render_attrs(elt.attr) if elt.attr else ""
        children = (
            DOMStringCompat.render_children(elt.children)
            if elt.children
            else ""
        )

        if type_ == "fragment":
            return children

        if type_ in VOID_ELEMENTS:
            return f"<{type_}{attr}/>"

        if type_ == "escaped_html":
            return elt.markup  # type: ignore

        return f"<{type_}{attr}>{children}</{type_}>"

    @staticmethod
    def render_debug(elt: Elt) -> HTML:
        type_ = elt.type
        attr = DOMStringCompat.render_attrs(elt.attr) if elt.attr else ""
        children = (
            DOMStringCompat.render_children(elt.children)
            if elt.children
            else ""
        )

        if type_ in VOID_ELEMENTS:
            return f"<{type_}{attr}/>"

        if type_ == "escaped_html":
            return elt.markup  # type: ignore

        return f"<{type_}{attr}>{children}</{type_}>"
