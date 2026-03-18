from abc import ABC, abstractmethod

from django.utils.deconstruct import deconstructible

from wagtail.blocks.migrations.utils import formatted_list_child_generator


class BaseBlockOperation(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def apply(self, block_value):
        """Logic for forward migration"""
        pass

    @abstractmethod
    def reverse(self, block_value):
        """
        Logic for backward migration.
        Should perfectly undo the changes made in apply().
        """
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
        # Forward: Rename A -> B
        for child in block_value:
            if child["type"] == self.old_name:
                child["type"] = self.new_name
        return block_value

    def reverse(self, block_value):
        # Backward: Rename B -> A
        for child in block_value:
            if child["type"] == self.new_name:
                child["type"] = self.old_name
        return block_value

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
        return {
            (self.new_name if k == self.old_name else k): v
            for k, v in block_value.items()
        }

    def reverse(self, block_value):
        return {
            (self.old_name if k == self.new_name else k): v
            for k, v in block_value.items()
        }

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

    def reverse(self, block_value):
        raise NotImplementedError("RemoveStreamChildrenOperation is irreversible.")

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
        return [child for child in block_value if child["type"] != self.name]

    def reverse(self, block_value):
        raise NotImplementedError(
            "RemoveStreamChildrenOperation is irreversible (data was deleted)."
        )

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

    def apply(self, block_value):
        candidate_blocks = []
        mapped_block_value = []
        for child_block in block_value:
            if child_block["type"] == self.block_name:
                candidate_blocks.append(child_block)
            else:
                mapped_block_value.append(child_block)

        list_items = self.map_temp_blocks_to_list_items(candidate_blocks)

        if list_items:
            new_list_block = {"type": self.list_block_name, "value": list_items}
            mapped_block_value.append(new_list_block)

        return mapped_block_value

    def map_temp_blocks_to_list_items(self, blocks):
        list_items = []
        for block in blocks:
            list_items.append({**block, "type": "item"})
        return list_items

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

    def __init__(self, block_name, struct_block_name):
        super().__init__()
        self.block_name = block_name
        self.struct_block_name = struct_block_name

    def apply(self, block_value):
        mapped = []
        for child in block_value:
            if child["type"] == self.block_name:
                mapped.append(
                    {
                        **child,
                        "type": self.struct_block_name,
                        "value": {self.block_name: child["value"]},
                    }
                )
            else:
                mapped.append(child)
        return mapped

    def reverse(self, block_value):
        mapped = []
        for child in block_value:
            if child["type"] == self.struct_block_name:
                mapped.append(
                    {
                        **child,
                        "type": self.block_name,
                        "value": child["value"][self.block_name],
                    }
                )
            else:
                mapped.append(child)
        return mapped

    @property
    def operation_name_fragment(self):
        return f"{self.block_name}_to_struct_{self.struct_block_name}"


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

    def reverse(self, block_value):
        # Unless we store the old value in the migration (which is hard),
        # altering a value is generally irreversible.
        raise NotImplementedError("AlterBlockValueOperation is irreversible.")

    @property
    def operation_name_fragment(self):
        return "alter_block_value"


@deconstructible
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
        mapped = []
        for child in block_value:
            if child["type"] == self.block_name:
                mapped.append(
                    {
                        **child,
                        "type": self.struct_block_name,
                        "value": {self.block_name: child["value"]},
                    }
                )
            else:
                mapped.append(child)
        return mapped

    def reverse(self, block_value):
        mapped = []
        for child in block_value:
            if child["type"] == self.struct_block_name:
                mapped.append(
                    {
                        **child,
                        "type": self.block_name,
                        "value": child["value"][self.block_name],
                    }
                )
            else:
                mapped.append(child)
        return mapped

    @property
    def operation_name_fragment(self):
        return f"{self.block_name}_to_struct_{self.struct_block_name}"


@deconstructible
class ListChildrenToStructBlockOperation(BaseBlockOperation):
    def __init__(self, block_name):
        super().__init__()
        self.block_name = block_name

    def apply(self, block_value):
        mapped_block_value = []
        for child_block in formatted_list_child_generator(block_value):
            mapped_block_value.append(
                {**child_block, "value": {self.block_name: child_block["value"]}}
            )
        return mapped_block_value

    def reverse(self, block_value):
        # Unwrap dictionary values back to raw list items
        return [
            {**child, "value": child["value"][self.block_name]} for child in block_value
        ]

    @property
    def operation_name_fragment(self):
        return f"list_block_items_to_{self.block_name}"
