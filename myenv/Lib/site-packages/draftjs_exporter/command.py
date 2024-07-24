from typing import List

from draftjs_exporter.types import Block


class Command:
    """
    A Command represents an operation that has to be executed
    on a block for it to be converted into an arbitrary number
    of HTML nodes.
    """

    __slots__ = ("name", "index", "data")

    def __init__(self, name: str, index: int, data: str = "") -> None:
        self.name = name
        self.index = index
        self.data = data

    def __str__(self) -> str:
        return f"<Command {self.name} {self.index} {self.data}>"

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def from_entity_ranges(block: Block) -> List["Command"]:
        """
        Creates a list of commands from a block’s list of entity ranges.
        Each range is converted to two commands: a start_* and a stop_*.
        """
        commands: List["Command"] = []
        for r in block["entityRanges"]:
            # Entity key is an integer in entity ranges, while a string in the entity map.
            data = str(r["key"])
            start = r["offset"]
            stop = start + r["length"]
            commands.append(Command("start_entity", start, data))
            commands.append(Command("stop_entity", stop, data))

        return commands

    @staticmethod
    def from_style_ranges(block: Block) -> List["Command"]:
        """
        Creates a list of commands from a block’s list of style ranges.
        Each range is converted to two commands: a start_* and a stop_*.
        """
        commands: List["Command"] = []
        for r in block["inlineStyleRanges"]:
            data = r["style"]
            start = r["offset"]
            stop = start + r["length"]
            commands.append(Command("start_inline_style", start, data))
            commands.append(Command("stop_inline_style", stop, data))
        return commands
