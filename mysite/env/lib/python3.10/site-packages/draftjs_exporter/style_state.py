from typing import List, Sequence

from draftjs_exporter.command import Command
from draftjs_exporter.constants import INLINE_STYLES
from draftjs_exporter.dom import DOM
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element


class StyleState:
    """
    Handles the creation of inline styles on elements.
    Receives inline_style commands, and generates the element's `style`
    attribute from those.
    """

    __slots__ = ("styles", "style_options")

    def __init__(self, style_options: OptionsMap) -> None:
        self.styles: List[str] = []
        self.style_options = style_options

    def apply(self, command: Command) -> None:
        if command.name == "start_inline_style":
            self.styles.append(command.data)
        elif command.name == "stop_inline_style":
            self.styles.remove(command.data)

    def is_empty(self) -> bool:
        return not self.styles

    def render_styles(
        self, decorated_node: Element, block: Block, blocks: Sequence[Block]
    ) -> Element:
        node = decorated_node
        if not self.is_empty():
            # This will mutate self.styles, but it’s going to be reset after rendering anyway.
            self.styles.sort(reverse=True)

            # Nest the tags.
            for style in self.styles:
                options = Options.get(
                    self.style_options, style, INLINE_STYLES.FALLBACK
                )
                props = dict(options.props)
                props["block"] = block
                props["blocks"] = blocks
                props["inline_style_range"] = {"style": style}
                node = DOM.create_element(options.element, props, node)

        return node
