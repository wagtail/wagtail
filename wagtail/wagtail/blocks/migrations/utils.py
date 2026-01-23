from wagtail.blocks import ListBlock, StreamBlock, StructBlock


class InvalidBlockDefError(Exception):
    """Exception for invalid block definitions"""

    def __init__(self, *args, instance=None, revision=None, **kwargs):
        # in the case of a revision pass both instance and revision
        self.instance = instance
        self.revision = revision
        super().__init__(*args, **kwargs)

    def __str__(self):
        message = ""
        if self.instance is not None:
            message += "Invalid block def in {} object ({})".format(
                self.instance.__class__.__name__, self.instance.id
            )
            if self.revision is not None:
                message += " for revision id ({}) created at {}".format(
                    self.revision.id,
                    self.revision.created_at,
                )
            if self.args:
                message += "\n"

        message += super().__str__()
        return message


def should_alter_block(block_name, block_path):
    # If the block is not at the start of `block_path`, then neither it nor its children are
    # blocks that we need to alter.
    return block_name == block_path[0]


def map_block_value(block_value, block_def, block_path, operation, **kwargs):
    """
    Maps the value of a block.

    Args:
        block_value:
            The value of the block. This would be a list or dict of children for structural blocks.
        block_def:
            The definition of the block.
        block_path:
            A '.' separated list of names of the blocks from the current block (not included) to
            the nested block of which the value will be passed to the operation.
        operation:
            An Operation class instance (extends `BaseBlockOperation`), which has an `apply` method
            for mapping values.

    Returns:
        mapped_value:
    """

    # If the `block_path` length is 0, that means we've reached the end of the block path, that
    # is, the block where we need to apply the operation. Note that we are asking the user to
    # pass "item" as part of the block path for list children, so it won't give rise to any
    # problems here.
    if len(block_path) == 0:
        return operation.apply(block_value)

    # Depending on whether the block is a ListBlock, StructBlock or StreamBlock we call a
    # different function to alter its children.

    if isinstance(block_def, StreamBlock):
        return map_stream_block_value(
            block_value,
            operation=operation,
            block_def=block_def,
            block_path=block_path,
            **kwargs,
        )

    elif isinstance(block_def, ListBlock):
        return map_list_block_value(
            block_value,
            operation=operation,
            block_def=block_def,
            block_path=block_path,
            **kwargs,
        )

    elif isinstance(block_def, StructBlock):
        return map_struct_block_value(
            block_value,
            operation=operation,
            block_def=block_def,
            block_path=block_path,
            **kwargs,
        )

    else:
        raise ValueError(f"Unexpected Structural Block: {block_value}")


def map_stream_block_value(stream_block_value, block_def, block_path, **kwargs):
    """
    Maps each child block in a StreamBlock value.

    Args:
        stream_block_value:
            The value of the StreamBlock, a list of child blocks
        block_def:
            The definition of the StreamBlock
        block_path:
            A '.' separated list of names of the blocks from the current block (not included) to
            the nested block of which the value will be passed to the operation.

    Returns
        mapped_value:
            The value of the StreamBlock after mapping all the children.
    """

    mapped_value = []
    for child_block in stream_block_value:

        if not should_alter_block(child_block["type"], block_path):
            mapped_value.append(child_block)

        else:
            try:
                child_block_def = block_def.child_blocks[child_block["type"]]
            except KeyError:
                raise InvalidBlockDefError(
                    "No current block def named {}".format(child_block["type"])
                )
            mapped_child_value = map_block_value(
                child_block["value"],
                block_def=child_block_def,
                block_path=block_path[1:],
                **kwargs,
            )
            mapped_value.append({**child_block, "value": mapped_child_value})

    return mapped_value


def map_struct_block_value(struct_block_value, block_def, block_path, **kwargs):
    """
    Maps each child block in a StructBlock value.

    Args:
        stream_block_value:
            The value of the StructBlock, a dict of child blocks
        block_def:
            The definition of the StructBlock
        block_path:
            A '.' separated list of names of the blocks from the current block (not included) to
            the nested block of which the value will be passed to the operation.

    Returns
        mapped_value:
            The value of the StructBlock after mapping all the children.
    """

    mapped_value = {}
    for key, child_value in struct_block_value.items():

        if not should_alter_block(key, block_path):
            mapped_value[key] = child_value

        else:
            try:
                child_block_def = block_def.child_blocks[key]
            except KeyError:
                raise InvalidBlockDefError(f"No current block def named {key}")
            altered_child_value = map_block_value(
                child_value,
                block_def=child_block_def,
                block_path=block_path[1:],
                **kwargs,
            )
            mapped_value[key] = altered_child_value

    return mapped_value


def map_list_block_value(list_block_value, block_def, block_path, **kwargs):
    """
    Maps each child block in a ListBlock value.

    Args:
        stream_block_value:
            The value of the ListBlock, a list of child blocks
        block_def:
            The definition of the ListBlock
        block_path:
            A '.' separated list of names of the blocks from the current block (not included) to
            the nested block of which the value will be passed to the operation.

    Returns
        mapped_value:
            The value of the ListBlock after mapping all the children.
    """

    mapped_value = []
    # In case data is in old list format
    for child_block in formatted_list_child_generator(list_block_value):

        mapped_child_value = map_block_value(
            child_block["value"],
            block_def=block_def.child_block,
            block_path=block_path[1:],
            **kwargs,
        )

        mapped_value.append({**child_block, "value": mapped_child_value})

    return mapped_value


def formatted_list_child_generator(list_block_value):
    is_old_format = False
    if not isinstance(list_block_value[0], dict):
        is_old_format = True
    elif "type" not in list_block_value[0] or list_block_value[0]["type"] != "item":
        is_old_format = True

    for child in list_block_value:
        if not is_old_format:
            yield child
        else:
            yield {"type": "item", "value": child}


def apply_changes_to_raw_data(
    raw_data, block_path_str, operation, streamfield, **kwargs
):
    """
    Applies changes to raw stream data

    Args:
        raw_data:
            The current stream data (a list of top level blocks)
        block_path_str:
            A '.' separated list of names of the blocks from the top level block to the nested
            block of which the value will be passed to the operation.

            eg:- 'simplestream.struct1' would point to,
                [..., { type: simplestream, value: [..., { type: struct1, value: {...} }] }]

            NOTE: If we're directly applying changes on the top level stream block, then this will
            be "".

            NOTE: When the path contains a ListBlock child, 'item' must be added to the block as
            the name of said child.

            eg:- 'list1.item.stream1' where the list child is a StructBlock would point to,
                [
                    ...,
                    {
                        type: list1,
                        value: [
                            {
                                type: item,
                                value: { ..., stream1: [...] }
                            },
                            ...
                        ]
                    }
                ]
        operation:
            A subclass of `operations.BaseBlockOperation`. It will have the `apply` method
            for applying changes to the matching block values.
        streamfield:
            The streamfield for which data is being migrated. This is used to get the definitions
            of the blocks.

    Returns:
        altered_raw_data:
    """

    if block_path_str == "":
        # If block_path_str is "", we're directly applying the operation on the top level
        # streamblock.
        block_path = []
    else:
        block_path = block_path_str.split(".")
    block_def = streamfield.field.stream_block

    altered_raw_data = map_block_value(
        raw_data,
        block_def=block_def,
        block_path=block_path,
        operation=operation,
        **kwargs,
    )

    return altered_raw_data
