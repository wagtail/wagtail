import re
from typing import Optional

from draftjs_exporter.engines.base import Attr, DOMEngine
from draftjs_exporter.types import HTML, Element, Tag

try:
    from bs4 import BeautifulSoup

    # Cache empty soup so we can create tags in isolation without the performance overhead.
    soup = BeautifulSoup("", "html5lib")
except ImportError:
    pass

RENDER_RE = re.compile(r"</?(fragment|body|html|head)>")
RENDER_DEBUG_RE = re.compile(r"</?(body|html|head)>")


class DOM_HTML5LIB(DOMEngine):
    """
    html5lib implementation of the DOM API.
    """

    @staticmethod
    def create_tag(type_: Tag, attr: Optional[Attr] = None) -> Element:
        if not attr:
            attr = {}

        return soup.new_tag(type_, **attr)

    @staticmethod
    def parse_html(markup: HTML) -> Element:
        return BeautifulSoup(markup, "html5lib")

    @staticmethod
    def append_child(elt: Element, child: Element) -> None:
        elt.append(child)

    @staticmethod
    def render(elt: Element) -> HTML:
        return RENDER_RE.sub("", str(elt))

    @staticmethod
    def render_debug(elt: Element) -> HTML:
        return RENDER_DEBUG_RE.sub("", str(elt))
