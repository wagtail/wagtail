from collections import defaultdict
from importlib import import_module


class BlockDefinitionLookup:
    """
    A utility for constructing StreamField Block objects in migrations, starting from
    a compact representation that avoids repeating the same definition whenever a
    block is re-used in multiple places over the block definition tree.

    The underlying data is a dict of block definitions, such as:
    ```
    {
        0: ("wagtail.blocks.CharBlock", [], {"required": True}),
        1: ("wagtail.blocks.RichTextBlock", [], {}),
        2: ("wagtail.blocks.StreamBlock", [
            [
                ("heading", 0),
                ("paragraph", 1),
            ],
        ], {}),
    }
    ```

    where each definition is a tuple of (module_path, args, kwargs) similar to that
    returned by `deconstruct` - with the difference that any block objects appearing
    in args / kwargs may be substituted with an index into the lookup table that
    points to that block's definition. Any block class that wants to support such
    substitutions should implement a static/class method
    `construct_from_lookup(lookup, *args, **kwargs)`, where `lookup` is
    the `BlockDefinitionLookup` instance. The method should return a block instance
    constructed from the provided arguments (after performing any lookups).
    """

    def __init__(self, blocks):
        self.blocks = blocks
        self.block_classes = {}

    def get_block(self, index):
        path, args, kwargs = self.blocks[index]
        try:
            cls = self.block_classes[path]
        except KeyError:
            module_name, class_name = path.rsplit(".", 1)
            module = import_module(module_name)
            cls = self.block_classes[path] = getattr(module, class_name)

        return cls.construct_from_lookup(self, *args, **kwargs)


class BlockDefinitionLookupBuilder:
    """
    Helper for constructing the lookup data used by BlockDefinitionLookup
    """

    def __init__(self):
        self.blocks = []

        # Lookup table mapping the deconstructed tuple forms of blocks (as obtained from
        # `block.deconstruct_with_lookup`) to their index in the `blocks` list. These
        # tuples can be compared for equality, but not hashed, so we cannot use them as
        # dict keys; instead, we index them on the first tuple element (the module path)
        # and maintain a list of (index, deconstructed_tuple) pairs for each one.
        self.block_indexes_by_type = defaultdict(list)

    def add_block(self, block):
        """
        Add a block to the lookup table, returning an index that can be used to refer to it
        """
        deconstructed = block.deconstruct_with_lookup(self)

        # Check if we've already seen this block definition
        block_indexes = self.block_indexes_by_type[deconstructed[0]]
        for index, existing_deconstructed in block_indexes:
            if existing_deconstructed == deconstructed:
                return index

        # If not, add it to the lookup table
        index = len(self.blocks)
        self.blocks.append(deconstructed)
        block_indexes.append((index, deconstructed))
        return index

    def get_lookup_as_dict(self):
        return dict(enumerate(self.blocks))
