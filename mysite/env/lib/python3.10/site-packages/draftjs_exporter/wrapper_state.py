from typing import List, Optional, Sequence, Union

from draftjs_exporter.constants import BLOCK_TYPES
from draftjs_exporter.dom import DOM
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import Block, Element, Props, RenderableType


class Wrapper:
    """
    A wrapper is an element that wraps other nodes. It gets created
    when the depth of a block is different than 0, so the DOM elements
    have the appropriate amount of nesting.
    """

    __slots__ = ("depth", "last_child", "type", "props", "elt")

    def __init__(self, depth: int, options: Optional[Options] = None) -> None:
        self.depth = depth
        self.last_child = None

        if options:
            self.type = options.wrapper
            self.props = options.wrapper_props

            wrapper_props = dict(self.props) if self.props else {}
            wrapper_props["block"] = {"type": options.type, "depth": depth}

            self.elt = DOM.create_element(self.type, wrapper_props)
        else:
            self.type = None
            self.props = None
            self.elt = DOM.create_element()

    def is_different(
        self, depth: int, type_: RenderableType, props: Optional[Props]
    ) -> bool:
        return depth > self.depth or type_ != self.type or props != self.props


class WrapperStack:
    """
    Stack data structure for element wrappers.
    The bottom of the stack contains the elements closest to the page body.
    The top of the stack contains the most nested nodes.
    """

    __slots__ = "stack"

    def __init__(self) -> None:
        self.stack: List[Wrapper] = []

    def __str__(self) -> str:
        return str(self.stack)

    def length(self) -> int:
        return len(self.stack)

    def append(self, wrapper: Wrapper) -> None:
        return self.stack.append(wrapper)

    def get(self, index: int) -> Wrapper:
        return self.stack[index]

    def slice(self, length: int) -> None:
        self.stack = self.stack[:length]

    def head(self) -> Wrapper:
        if self.length() > 0:
            wrapper = self.stack[-1]
        else:
            wrapper = Wrapper(-1)

        return wrapper

    def tail(self) -> Wrapper:
        return self.stack[0]


class WrapperState:
    """
    This class does the initial node building for the tree.
    It sets elements with the right tag, text content, and props.
    It adds a wrapper element around elements, if required.
    """

    __slots__ = ("block_options", "blocks", "stack")

    def __init__(
        self, block_options: OptionsMap, blocks: Sequence[Block]
    ) -> None:
        self.block_options = block_options
        self.blocks = blocks
        self.stack = WrapperStack()

    def __str__(self) -> str:
        return f"<WrapperState: {self.stack}>"

    def element_for(
        self, block: Block, block_content: Union[Element, Sequence[Element]]
    ) -> Element:
        type_ = block["type"] if "type" in block else "unstyled"
        depth = block["depth"] if "depth" in block else 0
        options = Options.get(self.block_options, type_, BLOCK_TYPES.FALLBACK)
        props = dict(options.props)
        props["block"] = block
        props["blocks"] = self.blocks

        # Make an element from the options specified in the block map.
        elt = DOM.create_element(options.element, props, block_content)

        parent = self.parent_for(options, depth, elt)

        return parent

    def parent_for(self, options: Options, depth: int, elt: Element) -> Element:
        if options.wrapper:
            parent = self.get_wrapper_elt(options, depth)
            DOM.append_child(parent, elt)
            self.stack.stack[-1].last_child = elt
        else:
            # Reset the stack if there is no wrapper.
            if self.stack.length() > 0:
                self.stack = WrapperStack()
            parent = elt

        return parent

    def get_wrapper_elt(self, options: Options, depth: int) -> Element:
        head = self.stack.head()
        if head.is_different(depth, options.wrapper, options.wrapper_props):
            self.update_stack(options, depth)

        # If depth is lower than the maximum, we cut the stack.
        if depth < head.depth:
            self.stack.slice(depth + 1)

        return self.stack.get(depth).elt

    def update_stack(self, options: Options, depth: int) -> None:
        if depth >= self.stack.length():
            # If the depth is gte the stack length, we need more wrappers.
            depth_levels = range(self.stack.length(), depth + 1)

            for level in depth_levels:
                new_wrapper = Wrapper(level, options)

                # Determine where to append the new wrapper.
                if self.stack.head().last_child is None:
                    # If there is no content in the current wrapper, we need
                    # to add an intermediary node.
                    props = dict(options.props)
                    props["block"] = {
                        "type": options.type,
                        "depth": depth,
                        "data": {},
                    }
                    props["blocks"] = self.blocks

                    wrapper_parent = DOM.create_element(options.element, props)
                    DOM.append_child(self.stack.head().elt, wrapper_parent)
                else:
                    # Otherwise we can append at the end of the last child.
                    wrapper_parent = self.stack.head().last_child

                DOM.append_child(wrapper_parent, new_wrapper.elt)

                self.stack.append(new_wrapper)
        else:
            # Cut the stack to where it now stops, and add new wrapper.
            self.stack.slice(depth)
            self.stack.append(Wrapper(depth, options))
