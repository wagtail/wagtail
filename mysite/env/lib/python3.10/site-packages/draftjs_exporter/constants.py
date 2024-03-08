# http://stackoverflow.com/a/22723724/1798491
class Enum:
    __slots__ = "elements"

    def __init__(self, *elements: str) -> None:
        self.elements = tuple(elements)

    def __getattr__(self, name: str) -> str:
        if name not in self.elements:
            raise AttributeError(f"'Enum' has no attribute '{name}'")

        return name


# https://github.com/facebook/draft-js/blob/master/src/model/constants/DraftBlockType.js
class BLOCK_TYPES:
    UNSTYLED = "unstyled"
    HEADER_ONE = "header-one"
    HEADER_TWO = "header-two"
    HEADER_THREE = "header-three"
    HEADER_FOUR = "header-four"
    HEADER_FIVE = "header-five"
    HEADER_SIX = "header-six"
    UNORDERED_LIST_ITEM = "unordered-list-item"
    ORDERED_LIST_ITEM = "ordered-list-item"
    BLOCKQUOTE = "blockquote"
    PRE = "pre"
    CODE = "code-block"
    ATOMIC = "atomic"
    # Special type to configure handling of missing components.
    FALLBACK = "fallback"


ENTITY_TYPES = Enum(
    "LINK",
    "DOCUMENT",
    "IMAGE",
    "EMBED",
    "HORIZONTAL_RULE",
    # Special type to configure handling of missing components.
    "FALLBACK",
)

INLINE_STYLES = Enum(
    "BOLD",
    "CODE",
    "ITALIC",
    "UNDERLINE",
    "STRIKETHROUGH",
    "SUPERSCRIPT",
    "SUBSCRIPT",
    "MARK",
    "QUOTATION",
    "SMALL",
    "SAMPLE",
    "INSERT",
    "DELETE",
    "KEYBOARD",
    # Special type to configure handling of missing components.
    "FALLBACK",
)
