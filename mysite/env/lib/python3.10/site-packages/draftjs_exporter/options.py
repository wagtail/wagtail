from typing import Any, Dict, Optional

from draftjs_exporter.constants import BLOCK_TYPES, ENTITY_TYPES, INLINE_STYLES
from draftjs_exporter.error import ConfigException
from draftjs_exporter.types import ConfigMap, Props, RenderableType

# Internal equivalent of a ConfigMap.
OptionsMap = Dict[str, "Options"]


class Options:
    """
    Facilitates querying configuration from a config map.
    """

    __slots__ = ("type", "element", "props", "wrapper", "wrapper_props")

    def __init__(
        self,
        type_: str,
        element: RenderableType,
        props: Optional[Props] = None,
        wrapper: RenderableType = None,
        wrapper_props: Optional[Props] = None,
    ) -> None:
        self.type = type_
        self.element = element
        self.props = props if props else {}
        self.wrapper = wrapper
        self.wrapper_props = wrapper_props

    def __str__(self) -> str:
        return f"<Options {self.type} {self.element} {self.props} {self.wrapper} {self.wrapper_props}>"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: Any) -> bool:
        """
        Equality used in test code only, not to be relied on for the exporter.
        """
        return str(self) == str(other)

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(str(self))

    @staticmethod
    def create(kind_map: ConfigMap, type_: str, fallback_key: str) -> "Options":
        """
        Create an Options object from any mapping.
        """
        if type_ not in kind_map:
            if fallback_key not in kind_map:
                raise ConfigException(
                    f'"{type_}" is not in the config and has no fallback'
                )

            config = kind_map[fallback_key]
        else:
            config = kind_map[type_]

        if isinstance(config, dict):
            if "element" not in config:
                raise ConfigException(f'"{type_}" does not define an element')

            opts = Options(type_, **config)
        else:
            opts = Options(type_, config)

        return opts

    @staticmethod
    def map(kind_map: ConfigMap, fallback_key: str) -> OptionsMap:
        options = {}
        for type_ in kind_map:
            options[type_] = Options.create(kind_map, type_, fallback_key)

        return options

    @staticmethod
    def map_blocks(block_map: ConfigMap) -> OptionsMap:
        return Options.map(block_map, BLOCK_TYPES.FALLBACK)

    @staticmethod
    def map_styles(style_map: ConfigMap) -> OptionsMap:
        return Options.map(style_map, INLINE_STYLES.FALLBACK)

    @staticmethod
    def map_entities(entity_map: ConfigMap) -> OptionsMap:
        return Options.map(entity_map, ENTITY_TYPES.FALLBACK)

    @staticmethod
    def get(options: OptionsMap, type_: str, fallback_key: str) -> "Options":
        try:
            return options[type_]
        except KeyError:
            try:
                return options[fallback_key]
            except KeyError:
                raise ConfigException(
                    f'"{type_}" is not in the config and has no fallback'
                )
