from abc import ABC, abstractmethod
from wagtail.blocks.migrations.utils import formatted_list_child_generator
from django.utils.deconstruct import deconstructible


class BaseBlockOperation(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def apply(self, block_value):
        pass

    @property
    @abstractmethod
    def operation_name_fragment(self):
        pass


@deconstructible
class RenameStreamChildrenOperation(BaseBlockOperation):
    """Renames all StreamBlock children of the given type

    Note:
        The `block_path_str` when using this operation should point to the parent StreamBlock
        which contains the blocks to be renamed, not the block being renamed.

    Attributes:
        old_name (str): name of the child block type to be renamed
        new_name (str): new name to rename to
    """

    def __init__(self, old_name, new_name):
        super().__init__()
        self.old_name = old_name
        self.new_name = new_name

    def apply(self, block_value):
        mapped_block_value = []
        for child_block in block_value:
            if child_block["type"] == self.old_name:
                mapped_block_value.append({**child_block, "type": self.new_name})
            else:
                mapped_block_value.append(child_block)
        return mapped_block_value

    @property
    def operation_name_fragment(self):
        return f"rename_{self.old_name}_to_{self.new_name}"


@deconstructible
class RenameStructChildrenOperation(BaseBlockOperation):
    """Renames all StructBlock children of the given type

    Note:
        The `block_path_str` when using this operation should point to the parent StructBlock
        which contains the blocks to be renamed, not the block being renamed.

    Attributes:
        old_name (str): name of the child block type to be renamed
        new_name (str): new name to rename to
    """

    def __init__(self, old_name, new_name):
        super().__init__()
        self.old_name = old_name
        self.new_name = new_name

    def apply(self, block_value):
        mapped_block_value = {}
        for child_key, child_value in block_value.items():
            if child_key == self.old_name:
                mapped_block_value[self.new_name] = child_value
            else:
                mapped_block_value[child_key] = child_value
        return mapped_block_value

    @property
    def operation_name_fragment(self):
        return f"rename_{self.old_name}_to_{self.new_name}"


@deconstructible
class RemoveStreamChildrenOperation(BaseBlockOperation):
    """Removes all StreamBlock children of the given type

    Note:
        The `block_path_str` when using this operation should point to the parent StreamBlock
        which contains the blocks to be removed, not the block being removed.

    Attributes:
        name (str): name of the child block type to be removed
    """

    def __init__(self, name):
        super().__init__()
        self.name = name

    def apply(self, block_value):
        return [
            child_block
            for child_block in block_value
            if child_block["type"] != self.name
        ]

    @property
    def operation_name_fragment(self):
        return f"remove_{self.name}"


@deconstructible
class RemoveStructChildrenOperation(BaseBlockOperation):
    """Removes all StructBlock children of the given type

    Note:
        The `block_path_str` when using this operation should point to the parent StructBlock
        which contains the blocks to be removed, not the block being removed.

    Attributes:
        name (str): name of the child block type to be removed
    """

    def __init__(self, name):
        super().__init__()
        self.name = name

    def apply(self, block_value):
        return {
            child_key: child_value
            for child_key, child_value in block_value.items()
            if child_key != self.name
        }

    @property
    def operation_name_fragment(self):
        return f"remove_{self.name}"


class StreamChildrenToListBlockOperation(BaseBlockOperation):
    """Combines StreamBlock children of the given type into a new ListBlock

    Note:
        The `block_path_str` when using this operation should point to the parent StreamBlock
        which contains the blocks to be combined, not the child block itself.

    Attributes:
        block_name (str): name of the child block type to be combined
        list_block_name (str): name of the new ListBlock type
    """

    def __init__(self, block_name, list_block_name):
        super().__init__()
        self.block_name = block_name
        self.list_block_name = list_block_name
        self.temp_blocks = []

    def apply(self, block_value):
        mapped_block_value = []
        for child_block in block_value:
            if child_block["type"] == self.block_name:
                self.temp_blocks.append(child_block)
            else:
                mapped_block_value.append(child_block)

        self.map_temp_blocks_to_list_items()

        if self.temp_blocks:
            new_list_block = {"type": self.list_block_name, "value": self.temp_blocks}
            mapped_block_value.append(new_list_block)

        return mapped_block_value

    def map_temp_blocks_to_list_items(self):
        new_temp_blocks = []
        for block in self.temp_blocks:
            new_temp_blocks.append({**block, "type": "item"})
        self.temp_blocks = new_temp_blocks

    @property
    def operation_name_fragment(self):
        return f"{self.block_name}_to_list_block_{self.list_block_name}"


class StreamChildrenToStreamBlockOperation(BaseBlockOperation):
    """Combines StreamBlock children of the given types into a new StreamBlock

    Note:
        The `block_path_str` when using this operation should point to the parent StreamBlock
        which contains the blocks to be combined, not the child block itself.

    Attributes:
        block_names (:obj:`list` of :obj:`str`): names of the child block types to be combined
        stream_block_name (str): name of the new StreamBlock type
    """

    def __init__(self, block_names, stream_block_name):
        super().__init__()
        self.block_names = block_names
        self.stream_block_name = stream_block_name

    def apply(self, block_value):
        mapped_block_value = []
        stream_value = []

        for child_block in block_value:
            if child_block["type"] in self.block_names:
                stream_value.append(child_block)
            else:
                mapped_block_value.append(child_block)

        if stream_value:
            new_stream_block = {"type": self.stream_block_name, "value": stream_value}
            mapped_block_value.append(new_stream_block)

        return mapped_block_value

    @property
    def operation_name_fragment(self):
        return "{}_to_stream_block".format("_".join(self.block_names))


class AlterBlockValueOperation(BaseBlockOperation):
    """Alters the value of each block to the given value

    Attributes:
        new_value : new value to change to
    """

    def __init__(self, new_value):
        super().__init__()
        self.new_value = new_value

    def apply(self, block_value):
        return self.new_value

    @property
    def operation_name_fragment(self):
        return "alter_block_value"


class StreamChildrenToStructBlockOperation(BaseBlockOperation):
    """Move each StreamBlock child of the given type inside a new StructBlock

    A new StructBlock will be created as a child of the parent StreamBlock for each child block of
    the given type, and then that child block will be moved from the parent StreamBlocks children
    inside the new StructBlock as a child of that StructBlock.

    Example:
        Consider the following StreamField definition::

            mystream = StreamField([("char1", CharBlock()) ...], ...)

        Then the stream data would look like the following::

            [
                ...
                { "type": "char1", "value": "Value1", ... },
                { "type": "char1", "value": "Value2", ... },
                ...
            ]

        And if we define the operation like this::

            StreamChildrenToStructBlockOperation("char1", "struct1")

        Our altered stream data would look like this::

            [
                ...
                { "type": "struct1", "value": { "char1": "Value1" } },
                { "type": "struct1", "value": { "char1": "Value2" } },
                ...
            ]

    Note:
        The `block_path_str` when using this operation should point to the parent StreamBlock
        which contains the blocks to be combined, not the child block itself.

    Note:
        Block ids are not preserved here since the new blocks are structurally different than the
        previous blocks.

    Attributes:
        block_names (str): names of the child block types to be combined
        struct_block_name (str): name of the new StructBlock type
    """

    def __init__(self, block_name, struct_block_name):
        super().__init__()
        self.block_name = block_name
        self.struct_block_name = struct_block_name

    def apply(self, block_value):
        mapped_block_value = []
        for child_block in block_value:
            if child_block["type"] == self.block_name:
                mapped_block_value.append(
                    {
                        **child_block,
                        "type": self.struct_block_name,
                        "value": {self.block_name: child_block["value"]},
                    }
                )
            else:
                mapped_block_value.append(child_block)
        return mapped_block_value

    @property
    def operation_name_fragment(self):
        return f"{self.block_name}_to_struct_block_{self.struct_block_name}"


class ListChildrenToStructBlockOperation(BaseBlockOperation):
    def __init__(self, block_name):
        super().__init__()
        self.block_name = block_name

    def apply(self, block_value):
        mapped_block_value = []

        # In case there is data from the old list format (wagtail < 2.16), we use the generator
        # to convert them into the new list format
        for child_block in formatted_list_child_generator(block_value):
            mapped_block_value.append(
                {**child_block, "value": {self.block_name: child_block["value"]}}
            )
        return mapped_block_value

    @property
    def operation_name_fragment(self):
        return f"list_block_items_to_{self.block_name}"
