(streamfield_data_migration_reference)=

# StreamField data migration reference

## wagtail.blocks.migrations.migrate_operation

### MigrateStreamData

```python
class MigrateStreamData(RunPython)
```

Subclass of RunPython for `StreamField` data migration operations

#### \_\_init\_\_

```python
def __init__(app_name,
             model_name,
             field_name,
             operations_and_block_paths,
             revisions_from=None,
             chunk_size=1024,
             **kwargs)
```

MigrateStreamData constructor

**Arguments**:

-   `app_name` _str_ - Name of the app.
-   `model_name` _str_ - Name of the model.
-   `field_name` _str_ - Name of the `StreamField`.
-   `operations_and_block_paths` _List[Tuple[operation, str]]_ - List of operations and the block paths to apply them to.
-   `revisions_from` _datetime, optional_ - Only revisions created from this date onwards will be updated. Passing `None` updates all revisions. Defaults to `None`. Note that live and latest revisions will be updated regardless of what value this takes.
-   `chunk_size` _int, optional_ - chunk size for `queryset.iterator` and `bulk_update`.
    Defaults to 1024.
-   `**kwargs` - atomic, elidable, hints for superclass `RunPython` can be given

**Example**:

Renaming a block named `field1` to `block1`:

```python
MigrateStreamData(
    app_name="blog",
    model_name="BlogPage",
    field_name="content",
    operations_and_block_paths=[
        (RenameStreamChildrenOperation(old_name="field1", new_name="block1"), ""),
    ],
    revisions_from=datetime.datetime(2022, 7, 25)
)
```

## wagtail.blocks.migrations.operations

(rename_stream_children_operation)=

### RenameStreamChildrenOperation

```python
class RenameStreamChildrenOperation(BaseBlockOperation)
```

Renames all `StreamBlock` children of the given type

**Notes**:

The `block_path_str` when using this operation should point to the parent `StreamBlock` which contains the blocks to be renamed, not the block being renamed.

**Attributes**:

-   `old_name` _str_ - name of the child block type to be renamed
-   `new_name` _str_ - new name to rename to

(rename_struct_children_operation)=

### RenameStructChildrenOperation

```python
class RenameStructChildrenOperation(BaseBlockOperation)
```

Renames all `StructBlock` children of the given type

**Notes**:

The `block_path_str` when using this operation should point to the parent `StructBlock` which contains the blocks to be renamed, not the block being renamed.

**Attributes**:

-   `old_name` _str_ - name of the child block type to be renamed
-   `new_name` _str_ - new name to rename to

(remove_stream_children_operation)=

### RemoveStreamChildrenOperation

```python
class RemoveStreamChildrenOperation(BaseBlockOperation)
```

Removes all `StreamBlock` children of the given type

**Notes**:

The `block_path_str` when using this operation should point to the parent `StreamBlock` which contains the blocks to be removed, not the block being removed.

**Attributes**:

-   `name` _str_ - name of the child block type to be removed

(remove_struct_children_operation)=

### RemoveStructChildrenOperation

```python
class RemoveStructChildrenOperation(BaseBlockOperation)
```

Removes all `StructBlock` children of the given type

**Notes**:

The `block_path_str` when using this operation should point to the parent `StructBlock` which contains the blocks to be removed, not the block being removed.

**Attributes**:

-   `name` _str_ - name of the child block type to be removed

(stream_children_to_list_block_operation)=

### StreamChildrenToListBlockOperation

```python
class StreamChildrenToListBlockOperation(BaseBlockOperation)
```

Combines `StreamBlock` children of the given type into a new `ListBlock`

**Notes**:

The `block_path_str` when using this operation should point to the parent `StreamBlock` which contains the blocks to be combined, not the child block itself.

**Attributes**:

-   `block_name` _str_ - name of the child block type to be combined
-   `list_block_name` _str_ - name of the new `ListBlock` type

(stream_children_to_stream_block_operation)=

### StreamChildrenToStreamBlockOperation

```python
class StreamChildrenToStreamBlockOperation(BaseBlockOperation)
```

Combines `StreamBlock` children of the given types into a new `StreamBlock`

**Notes**:

The `block_path_str` when using this operation should point to the parent `StreamBlock` which contains the blocks to be combined, not the child block itself.

**Attributes**:

-   `block_names` _[str]_ - names of the child block types to be combined
-   `stream_block_name` _str_ - name of the new `StreamBlock` type

(alter_block_value_operation)=

### AlterBlockValueOperation

```python
class AlterBlockValueOperation(BaseBlockOperation)
```

Alters the value of each block to the given value

**Attributes**:

-   `new_value`: new value to change to

(stream_children_to_struct_block_operation)=

### StreamChildrenToStructBlockOperation

```python
class StreamChildrenToStructBlockOperation(BaseBlockOperation)
```

Move each `StreamBlock` child of the given type inside a new `StructBlock`

A new `StructBlock` will be created as a child of the parent `StreamBlock` for each child block of the given type, and then that child block will be moved from the parent StreamBlocks children inside the new `StructBlock` as a child of that `StructBlock`.

**Example**:

Consider the following `StreamField` definition:

```python
mystream = StreamField([("char1", CharBlock()), ...], ...)
```

Then the stream data would look like the following:

```python
[
    ...,
    { "type": "char1", "value": "Value1", ... },
    { "type": "char1", "value": "Value2", ... },
    ...
]
```

And if we define the operation like this:

```python
StreamChildrenToStructBlockOperation("char1", "struct1")
```

Our altered stream data would look like this:

```python
[
    ...,
    { "type": "struct1", "value": { "char1": "Value1" } },
    { "type": "struct1", "value": { "char1": "Value2" } },
    ...,
]
```

**Notes**:

-   The `block_path_str` when using this operation should point to the parent `StreamBlock` which contains the blocks to be combined, not the child block itself.
-   Block ids are not preserved here since the new blocks are structurally different than the previous blocks.

**Attributes**:

-   `block_names` _str_ - names of the child block types to be combined
-   `struct_block_name` _str_ - name of the new `StructBlock` type

## wagtail.blocks.migrations.utils

### InvalidBlockDefError

```python
class InvalidBlockDefError(Exception)
```

Exception for invalid block definitions

#### map_block_value

```python
def map_block_value(block_value, block_def, block_path, operation, **kwargs)
```

Maps the value of a block.

**Arguments**:

-   `block_value`: The value of the block. This would be a list or dict of children for structural blocks.
-   `block_def`: The definition of the block.
-   `block_path`: A `"."` separated list of names of the blocks from the current block (not included) to the nested block of which the value will be passed to the operation.
-   `operation`: An Operation class instance (extends `BaseBlockOperation`), which has an `apply` method for mapping values.

**Returns**:

Transformed value

#### map_struct_block_value

```python
def map_struct_block_value(struct_block_value, block_def, block_path,
                           **kwargs)
```

Maps each child block in a `StructBlock` value.

**Arguments**:

-   `stream_block_value`: The value of the `StructBlock`, a dict of child blocks
-   `block_def`: The definition of the `StructBlock`
-   `block_path`: A `"."` separated list of names of the blocks from the current block (not included) to the nested block of which the value will be passed to the operation.

**Returns**:

-   mapped_value: The value of the `StructBlock` after transforming its children.

#### map_list_block_value

```python
def map_list_block_value(list_block_value, block_def, block_path, **kwargs)
```

Maps each child block in a `ListBlock` value.

**Arguments**:

-   `stream_block_value`: The value of the `ListBlock`, a list of child blocks
-   `block_def`: The definition of the `ListBlock`
-   `block_path`: A `"."` separated list of names of the blocks from the current block (not included) to the nested block of which the value will be passed to the operation.

**Returns**:

-   mapped_value: The value of the `ListBlock` after transforming all the children.

#### apply_changes_to_raw_data

```python
def apply_changes_to_raw_data(raw_data, block_path_str, operation, streamfield,
                              **kwargs)
```

Applies changes to raw stream data

**Arguments**:

-   `raw_data`: The current stream data (a list of top level blocks)
-   `block_path_str`: A `"."` separated list of names of the blocks from the top level block to the nested block of which the value will be passed to the operation.
-   `operation`: A subclass of `operations.BaseBlockOperation`. It will have the `apply` method for applying changes to the matching block values.
-   `streamfield`: The `StreamField` for which data is being migrated. This is used to get the definitions of the blocks.

**Returns**:

altered_raw_data:

## Block paths

Operations for `StreamField` data migrations defined in `wagtail.blocks.migrations` require a "block path" to determine which blocks they should be applied to.

```
block_path = "" | block_name ("." block_name)*
block_name = str
```

A block path is either:

-   the empty string, in which case the operation should be applied to the top-level stream; or
-   a `"."` (period) separated sequence of block names, where block names are the names given to the blocks in the `StreamField` definition.

Block names are the values associated with the `"type"` keys in the stream data's dictionary structures. As such, traversing or selecting `ListBlock` members requires the use of the `"item"` block name.

The value that an operation's `apply` method receives is the `"value"` member of the dict associated with the terminal block name in the block path.

For examples see [the tutorial](using_streamfield_migration_block_paths).
