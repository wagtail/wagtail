from itertools import groupby
from operator import attrgetter
from typing import List, Optional, Tuple

from draftjs_exporter.command import Command
from draftjs_exporter.composite_decorators import (
    render_decorators,
    should_render_decorators,
)
from draftjs_exporter.defaults import BLOCK_MAP, STYLE_MAP
from draftjs_exporter.dom import DOM
from draftjs_exporter.entity_state import EntityState
from draftjs_exporter.options import Options
from draftjs_exporter.style_state import StyleState
from draftjs_exporter.types import (
    Block,
    Config,
    ContentState,
    Element,
    EntityMap,
)
from draftjs_exporter.wrapper_state import WrapperState


class HTML:
    """
    Entry point of the exporter. Combines entity, wrapper and style state
    to generate the right HTML nodes.
    """

    __slots__ = (
        "composite_decorators",
        "entity_options",
        "block_options",
        "style_options",
    )

    def __init__(self, config: Optional[Config] = None) -> None:
        if config is None:
            config = {}

        self.composite_decorators = config.get("composite_decorators", [])

        self.entity_options = Options.map_entities(
            config.get("entity_decorators", {})
        )
        self.block_options = Options.map_blocks(
            config.get("block_map", BLOCK_MAP)
        )
        self.style_options = Options.map_styles(
            config.get("style_map", STYLE_MAP)
        )

        DOM.use(config.get("engine", DOM.STRING))

    def render(self, content_state: Optional[ContentState] = None) -> str:
        """
        Starts the export process on a given piece of content state.
        """
        if content_state is None:
            content_state = {}

        blocks = content_state.get("blocks", [])
        wrapper_state = WrapperState(self.block_options, blocks)
        document = DOM.create_element()
        entity_map = content_state.get("entityMap", {})
        min_depth = 0

        for block in blocks:
            # Assume a depth of 0 if it's not specified, like Draft.js would.
            depth = block["depth"] if "depth" in block else 0
            elt = self.render_block(block, entity_map, wrapper_state)

            if depth > min_depth:
                min_depth = depth

            # At level 0, append the element to the document.
            if depth == 0:
                DOM.append_child(document, elt)

        # If there is no block at depth 0, we need to add the wrapper that contains the whole tree to the document.
        if min_depth > 0 and wrapper_state.stack.length() != 0:
            DOM.append_child(document, wrapper_state.stack.tail().elt)

        return DOM.render(document)

    def render_block(
        self, block: Block, entity_map: EntityMap, wrapper_state: WrapperState
    ) -> Element:
        has_styles = "inlineStyleRanges" in block and block["inlineStyleRanges"]
        has_entities = "entityRanges" in block and block["entityRanges"]
        has_decorators = should_render_decorators(
            self.composite_decorators, block["text"]
        )

        if has_styles or has_entities:
            content = DOM.create_element()
            entity_state = EntityState(self.entity_options, entity_map)
            style_state = StyleState(self.style_options) if has_styles else None

            for (text, commands) in self.build_command_groups(block):
                for command in commands:
                    entity_state.apply(command)
                    if style_state:
                        style_state.apply(command)

                # Decorators are not rendered inside entities.
                if has_decorators and entity_state.has_no_entity():
                    decorated_node = render_decorators(
                        self.composite_decorators,
                        text,
                        block,
                        wrapper_state.blocks,
                    )
                else:
                    decorated_node = text

                if style_state:
                    styled_node = style_state.render_styles(
                        decorated_node, block, wrapper_state.blocks
                    )
                else:
                    styled_node = decorated_node
                entity_node = entity_state.render_entities(
                    styled_node, block, wrapper_state.blocks
                )

                if entity_node is not None:
                    DOM.append_child(content, entity_node)

                    # Check whether there actually are two different nodes, confirming we are not inserting an upcoming entity.
                    if (
                        styled_node != entity_node
                        and entity_state.has_no_entity()
                    ):
                        DOM.append_child(content, styled_node)
        # Fast track for blocks which do not contain styles nor entities, which is very common.
        elif has_decorators:
            content = render_decorators(
                self.composite_decorators,
                block["text"],
                block,
                wrapper_state.blocks,
            )
        else:
            content = block["text"]

        return wrapper_state.element_for(block, content)

    def build_command_groups(
        self, block: Block
    ) -> List[Tuple[str, List[Command]]]:
        """
        Creates block modification commands, grouped by start index,
        with the text to apply them on.
        """
        text = block["text"]

        commands = self.build_commands(block)
        grouped = groupby(commands, attrgetter("index"))
        listed = list(groupby(commands, attrgetter("index")))
        sliced = []

        i = 0
        for start_index, comms in grouped:
            if i < len(listed) - 1:
                stop_index = listed[i + 1][0]
                sliced.append((text[start_index:stop_index], list(comms)))
            else:
                sliced.append(("", list(comms)))
            i += 1

        return sliced

    def build_commands(self, block: Block) -> List[Command]:
        """
        Build all of the manipulation commands for a given block.
        - One pair to set the text.
        - Multiple pairs for styles.
        - Multiple pairs for entities.
        """
        style_commands = Command.from_style_ranges(block)
        entity_commands = Command.from_entity_ranges(block)
        styles_and_entities = style_commands + entity_commands
        styles_and_entities.sort(key=attrgetter("index"))

        return (
            [Command("start_text", 0)]
            + styles_and_entities
            + [Command("stop_text", len(block["text"]))]
        )
