from html import escape
from typing import List, Optional, Sequence, Union

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.types import HTML, Tag

# http://w3c.github.io/html/single-page.html#void-elements
# https://github.com/html5lib/html5lib-python/blob/0cae52b2073e3f2220db93a7650901f2200f2a13/html5lib/constants.py#L560
VOID_ELEMENTS = (
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
)


class Elt:
    """
    A DOM element that the string engine manipulates.
    This class doesn't do much, but the exporter relies on
    comparing elements by reference so it's useful nonetheless.
    """

    __slots__ = ("type", "attr", "children", "markup")

    def __init__(self, type_: Tag, attr: Optional[Attr], markup: HTML = None):
        self.type = type_
        self.attr = attr
        self.children: List["Elt"] = []
        self.markup = markup

    @staticmethod
    def from_html(markup: HTML) -> "Elt":
        return Elt("escaped_html", None, markup)


class DOMString(DOMEngine):
    """
    String concatenation implementation of the DOM API.
    """

    @staticmethod
    def create_tag(type_: Tag, attr: Optional[Attr] = None) -> Elt:
        return Elt(type_, attr)

    @staticmethod
    def parse_html(markup: HTML) -> Elt:
        """
        Allows inserting arbitrary HTML into the exporter output.
        Treats the HTML as if it had been escaped and was safe already.
        """
        return Elt.from_html(markup)

    @staticmethod
    def append_child(elt: Elt, child: Elt) -> None:
        # This check is necessary because the current wrapper_state implementation
        # has an issue where it inserts elements multiple times.
        # This must be skipped for text, which can be duplicated.
        is_existing_ref = child in elt.children and isinstance(child, Elt)
        if not is_existing_ref:
            elt.children.append(child)

    @staticmethod
    def render_attrs(attr: Attr) -> str:
        attrs = [f' {k}="{escape(v)}"' for k, v in attr.items()]
        return "".join(attrs)

    @staticmethod
    def render_children(children: Sequence[Union[HTML, Elt]]) -> HTML:
        return "".join(
            [
                DOMString.render(c)
                if isinstance(c, Elt)
                else escape(c, quote=False)
                for c in children
            ]
        )

    @staticmethod
    def render(elt: Elt) -> HTML:
        type_ = elt.type
        attr = DOMString.render_attrs(elt.attr) if elt.attr else ""
        children = (
            DOMString.render_children(elt.children) if elt.children else ""
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
        attr = DOMString.render_attrs(elt.attr) if elt.attr else ""
        children = (
            DOMString.render_children(elt.children) if elt.children else ""
        )

        if type_ in VOID_ELEMENTS:
            return f"<{type_}{attr}/>"

        if type_ == "escaped_html":
            return elt.markup  # type: ignore

        return f"<{type_}{attr}>{children}</{type_}>"
