import re
from typing import Optional

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.types import HTML, Tag

try:
    from lxml import etree, html
except ImportError:
    pass

NSMAP = {"xlink": "http://www.w3.org/1999/xlink"}

RENDER_RE = re.compile(r"</?fragment>")


class DOM_LXML(DOMEngine):
    """
    lxml implementation of the DOM API.
    """

    @staticmethod
    def create_tag(type_: Tag, attr: Optional[Attr] = None) -> etree.Element:
        nsmap = None

        if attr:
            if "xlink:href" in attr:
                attr[f"{{{NSMAP['xlink']}}}href"] = attr.pop("xlink:href")
                nsmap = NSMAP

        return etree.Element(type_, attrib=attr, nsmap=nsmap)

    @staticmethod
    def parse_html(markup: HTML) -> etree.Element:
        return html.fromstring(markup)

    @staticmethod
    def append_child(elt: etree.Element, child: etree.Element) -> None:
        if hasattr(child, "tag"):
            elt.append(child)
        else:
            c = etree.Element("fragment")
            c.text = child
            elt.append(c)

    @staticmethod
    def render(elt: etree.Element) -> HTML:
        return RENDER_RE.sub(
            "", etree.tostring(elt, method="html", encoding="unicode")
        )

    @staticmethod
    def render_debug(elt: etree.Element) -> HTML:
        return etree.tostring(elt, method="html", encoding="unicode")
