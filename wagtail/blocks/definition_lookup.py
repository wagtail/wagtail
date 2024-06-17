from importlib import import_module


class BlockDefinitionLookup:
    """
    A utility for constructing StreamField Block objects in migrations, starting from
    a compact representation that avoids repeating the same definition whenever a
    block is re-used in multiple places over the block definition tree.

    The underlying data is a list of block definitions, such as:
    ```
    [
        ("wagtail.blocks.CharBlock", [], {"required": True}),
        ("wagtail.blocks.RichTextBlock", [], {}),
        ("wagtail.blocks.StreamBlock", [
            [
                ("heading", 0),
                ("paragraph", 1),
            ],
        ], {}),
    ]
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
