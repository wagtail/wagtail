from collections import defaultdict
from importlib import import_module

from wagtail.blocks.base import BlockReference


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

    A cyclic definition is represented by an index that points back to an ancestor still
    being constructed; `get_block` hands back a lazy `BlockReference` for such a back-edge,
    so reconstruction stays finite.
    """

    def __init__(self, blocks):
        self.blocks = blocks
        self.block_classes = {}
        # Indexes currently being constructed (the construction stack). A child referring to
        # an index already on the stack is a back-edge closing a cycle; get_block returns a
        # lazy BlockReference for it rather than recursing, keeping construction finite.
        self._constructing = set()

    def get_block(self, index):
        if index in self._constructing:
            # Back-edge to an ancestor still being constructed: hand back a reference (a
            # leaf) so reconstruction does not recurse forever. It resolves to a fresh block
            # when a value operation needs it.
            return BlockReference(lambda i=index: self.get_block(i))

        self._constructing.add(index)
        try:
            path, args, kwargs = self.blocks[index]
            try:
                cls = self.block_classes[path]
            except KeyError:
                module_name, class_name = path.rsplit(".", 1)
                module = import_module(module_name)
                cls = self.block_classes[path] = getattr(module, class_name)
            block = cls.construct_from_lookup(self, *args, **kwargs)
        finally:
            self._constructing.discard(index)

        # Give the block the node identity of its lookup index, so the builder recognises
        # re-entry across the fresh instances a reference produces on each resolution
        # (different id(), same index). See Block._definition_id.
        block._definition_id = index
        return block


class BlockDefinitionLookupBuilder:
    """
    Helper for constructing the lookup data used by BlockDefinitionLookup
    """

    def __init__(self):
        self.blocks = []

        # Index of each block fully added, keyed by node identity (block._definition_id), so
        # the same node re-used in several places is stored once. Node identity (not id()) is
        # required because a block rebuilt from a cyclic lookup yields a fresh instance on
        # every reference resolution; those share a _definition_id but not an id(), and an
        # id()-keyed builder would fail to recognise the cycle and recurse forever.
        self.block_indexes_by_identity = {}

        # Nodes whose deconstruction is in progress, keyed by _definition_id. The value is the
        # slot reserved for the block (or None if nothing has needed it yet). Used to break
        # cyclic graphs: a back-reference to a node still being deconstructed reserves its slot
        # here instead of recursing forever.
        self.pending_block_indexes = {}

        # Already-stored definitions, for structural deduplication. The deconstructed tuples
        # compare for equality but are not hashable, so we bucket them by their first element
        # (the module path) and keep a list of (index, deconstructed_tuple) pairs per bucket.
        self.block_indexes_by_type = defaultdict(list)

    def add_block(self, block):
        """
        Add a block to the lookup table, returning an index that can be used to refer to it.

        A BlockReference is serialised as its target, so a reference never becomes a table
        entry of its own; a back-edge is simply an index pointing at an ancestor.
        """
        identity = block._definition_id

        # Case 1: already fully added.
        if identity in self.block_indexes_by_identity:
            return self.block_indexes_by_identity[identity]

        # Case 2: a back-reference to a block still being deconstructed. Reserve a real slot
        # for it now (a placeholder, filled in when its own add_block call completes).
        if identity in self.pending_block_indexes:
            reserved_index = self.pending_block_indexes[identity]
            if reserved_index is None:
                reserved_index = len(self.blocks)
                self.blocks.append(None)
                self.pending_block_indexes[identity] = reserved_index
            return reserved_index

        # Case 3: first encounter. Mark as pending (no slot yet), then deconstruct, which
        # recurses into children and may reserve our slot via case 2.
        self.pending_block_indexes[identity] = None
        deconstructed = block.deconstruct_with_lookup(self)
        reserved_index = self.pending_block_indexes.pop(identity)

        block_indexes = self.block_indexes_by_type[deconstructed[0]]
        if reserved_index is None:
            # Nothing referred back to us, so we may reuse an identical definition.
            for existing_index, existing_deconstructed in block_indexes:
                if existing_deconstructed == deconstructed:
                    self.block_indexes_by_identity[identity] = existing_index
                    return existing_index
            index = len(self.blocks)
            self.blocks.append(deconstructed)
        else:
            # A back-reference reserved this slot (a cycle); fill it in, without dedup.
            index = reserved_index
            self.blocks[index] = deconstructed

        self.block_indexes_by_identity[identity] = index
        block_indexes.append((index, deconstructed))
        return index

    def get_lookup_as_dict(self):
        return dict(enumerate(self.blocks))
