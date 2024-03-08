from typing import List, Optional, Sequence

from draftjs_exporter.command import Command
from draftjs_exporter.constants import ENTITY_TYPES
from draftjs_exporter.dom import DOM
from draftjs_exporter.error import ExporterException
from draftjs_exporter.options import Options, OptionsMap
from draftjs_exporter.types import (
    Block,
    Element,
    EntityDetails,
    EntityKey,
    EntityMap,
)


class EntityException(ExporterException):
    pass


class EntityState:
    __slots__ = (
        "entity_options",
        "entity_map",
        "entity_stack",
        "completed_entity",
        "element_stack",
    )

    def __init__(
        self, entity_options: OptionsMap, entity_map: EntityMap
    ) -> None:
        self.entity_options = entity_options
        self.entity_map = entity_map

        self.entity_stack: List[EntityKey] = []
        self.completed_entity: Optional[EntityKey] = None
        self.element_stack: List[Element] = []

    def apply(self, command: Command) -> None:
        if command.name == "start_entity":
            self.entity_stack.append(command.data)
        elif command.name == "stop_entity":
            expected_entity = self.entity_stack[-1]

            if command.data != expected_entity:
                raise EntityException(
                    f"Expected {expected_entity}, got {command.data}"
                )

            self.completed_entity = self.entity_stack.pop()

    def has_entity(self) -> List[EntityKey]:
        return self.entity_stack

    def has_no_entity(self) -> bool:
        return not self.entity_stack

    def get_entity_details(self, entity_key: EntityKey) -> EntityDetails:
        details = self.entity_map.get(entity_key)

        if details is None:
            raise EntityException(
                f'Entity "{entity_key}" does not exist in the entityMap'
            )

        return details

    def render_entities(
        self, style_node: Element, block: Block, blocks: Sequence[Block]
    ) -> Element:
        # We have a complete (start, stop) entity to render.
        if self.completed_entity is not None:
            entity_details = self.get_entity_details(self.completed_entity)
            options = Options.get(
                self.entity_options,
                entity_details["type"],
                ENTITY_TYPES.FALLBACK,
            )
            props = entity_details["data"].copy()
            props["entity"] = {
                "type": entity_details["type"],
                "mutability": entity_details["mutability"]
                if "mutability" in entity_details
                else None,
                "block": block,
                "blocks": blocks,
                "entity_range": {"key": self.completed_entity},
            }

            if len(self.element_stack) == 1:
                children = self.element_stack[0]
            else:
                children = DOM.create_element()

                for n in self.element_stack:
                    DOM.append_child(children, n)

            self.completed_entity = None
            self.element_stack = []

            # Is there still another entity? (adjacent) if so add the current style_node for it.
            if self.has_entity():
                self.element_stack.append(style_node)

            return DOM.create_element(options.element, props, children)

        if self.has_entity():
            self.element_stack.append(style_node)
            return None

        return style_node
