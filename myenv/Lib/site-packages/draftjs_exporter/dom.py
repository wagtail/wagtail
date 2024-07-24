import re
from typing import Any, Optional

from draftjs_exporter.engines.base import DOMEngine
from draftjs_exporter.types import HTML, Element, Props, RenderableType
from draftjs_exporter.utils.module_loading import import_string

# https://gist.github.com/yahyaKacem/8170675
_first_cap_re = re.compile(r"(.)([A-Z][a-z]+)")
_all_cap_re = re.compile("([a-z0-9])([A-Z])")


class DOM:
    """
    Component building API, abstracting the DOM implementation.
    """

    HTML5LIB = "draftjs_exporter.engines.html5lib.DOM_HTML5LIB"
    LXML = "draftjs_exporter.engines.lxml.DOM_LXML"
    STRING = "draftjs_exporter.engines.string.DOMString"
    STRING_COMPAT = "draftjs_exporter.engines.string_compat.DOMStringCompat"

    dom: DOMEngine = None  # type: ignore

    @staticmethod
    def camel_to_dash(camel_cased_str: str) -> str:
        sub2 = _first_cap_re.sub(r"\1-\2", camel_cased_str)
        dashed_case_str = _all_cap_re.sub(r"\1-\2", sub2).lower()
        return dashed_case_str.replace("--", "-")

    @classmethod
    def use(cls, engine: str) -> None:
        """
        Choose which DOM implementation to use.
        """
        cls.dom = import_string(engine)

    @classmethod
    def create_element(
        cls,
        type_: RenderableType = None,
        props: Optional[Props] = None,
        *elt_children: Optional[Element],
    ) -> Element:
        """
        Signature inspired by React.createElement.
        createElement(
          string/Component type,
          [dict props],
          [children ...]
        )
        https://facebook.github.io/react/docs/top-level-api.html#react.createelement
        """
        # Create an empty document fragment.
        if not type_:
            return cls.dom.create_tag("fragment")

        if props is None:
            props = {}

        # If the first element of children is a list, we use it as the list.
        if len(elt_children) and isinstance(elt_children[0], (list, tuple)):
            children = elt_children[0]
        else:
            children = elt_children

        # The children prop is the first child if there is only one.
        props["children"] = children[0] if len(children) == 1 else children

        if callable(type_):
            # Function component, via def or lambda.
            elt = type_(props)
        else:
            # Raw tag, as a string.
            attributes = {}

            # Never render those attributes on a raw tag.
            props.pop("children", None)
            props.pop("block", None)
            props.pop("blocks", None)
            props.pop("entity", None)
            props.pop("inline_style_range", None)

            # Convert style object to style string, like the DOM would do.
            if "style" in props and isinstance(props["style"], dict):
                rules = [
                    f"{DOM.camel_to_dash(s)}: {v};"
                    for s, v in props["style"].items()
                ]
                props["style"] = "".join(rules)

            # Convert props to HTML attributes.
            for key in props:
                if props[key] is False:
                    props[key] = "false"

                if props[key] is True:
                    props[key] = "true"

                if props[key] is not None:
                    attributes[key] = str(props[key])

            elt = cls.dom.create_tag(type_, attributes)

            # Append the children inside the element.
            for child in children:
                if child not in (None, ""):
                    cls.append_child(elt, child)

        # If elt is "empty", create a fragment anyway to add children.
        if elt in (None, ""):
            elt = cls.dom.create_tag("fragment")

        return elt

    @classmethod
    def parse_html(cls, markup: HTML) -> Element:
        return cls.dom.parse_html(markup)

    @classmethod
    def append_child(cls, elt: Element, child: Element) -> Any:
        return cls.dom.append_child(elt, child)

    @classmethod
    def render(cls, elt: Element) -> HTML:
        return cls.dom.render(elt)

    @classmethod
    def render_debug(cls, elt: Element) -> HTML:
        return cls.dom.render_debug(elt)
