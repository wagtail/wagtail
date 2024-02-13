(streamfield_migrations)=

# StreamField migrations

(streamfield_migrating_richtext)=

## Migrating RichTextFields to StreamField

If you change an existing RichTextField to a StreamField, the database migration will complete with no errors, since both fields use a text column within the database. However, StreamField uses a JSON representation for its data, so the existing text requires an extra conversion step to become accessible again. For this to work, the StreamField needs to include a RichTextBlock as one of the available block types. Create the migration as normal using `./manage.py makemigrations`, then edit it as follows (in this example, the 'body' field of the `demo.BlogPage` model is being converted to a StreamField with a RichTextBlock named `rich_text`):

```python
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations

import wagtail.blocks
import wagtail.fields


def convert_to_streamfield(apps, schema_editor):
    BlogPage = apps.get_model("demo", "BlogPage")
    for page in BlogPage.objects.all():
        page.body = json.dumps(
            [{"type": "rich_text", "value": page.body}],
            cls=DjangoJSONEncoder
        )
        page.save()


def convert_to_richtext(apps, schema_editor):
    BlogPage = apps.get_model("demo", "BlogPage")
    for page in BlogPage.objects.all():
        if page.body:
            stream = json.loads(page.body)
            page.body = "".join([
                child["value"] for child in stream
                if child["type"] == "rich_text"
            ])
            page.save()


class Migration(migrations.Migration):

    dependencies = [
        # leave the dependency line from the generated migration intact!
        ("demo", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            convert_to_streamfield,
            convert_to_richtext,
        ),

        # leave the generated AlterField intact!
        migrations.AlterField(
            model_name="BlogPage",
            name="body",
            field=wagtail.fields.StreamField(
                [("rich_text", wagtail.blocks.RichTextBlock())],
            ),
        ),
    ]
```

Note that the above migration will work on published Page objects only. If you also need to migrate draft pages and page revisions, then edit the migration as in the following example instead:

```python
import json

from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations

import wagtail.blocks
import wagtail.fields


def page_to_streamfield(page):
    changed = False
    try:
        json.loads(page.body)
    except ValueError:
        page.body = json.dumps(
            [{"type": "rich_text", "value": page.body}],
        )
        changed = True
    else:
        # It's already valid JSON. Leave it.
        pass

    return page, changed


def pagerevision_to_streamfield(revision_data):
    changed = False
    body = revision_data.get("body")
    if body:
        try:
            json.loads(body)
        except ValueError:
            revision_data["body"] = json.dumps(
                [{
                    "value": body,
                    "type": "rich_text"
                }],
                cls=DjangoJSONEncoder)
            changed = True
        else:
            # It's already valid JSON. Leave it.
            pass
    return revision_data, changed


def page_to_richtext(page):
    changed = False
    if page.body:
        try:
            body_data = json.loads(page.body)
        except ValueError:
            # It's not apparently a StreamField. Leave it.
            pass
        else:
            page.body = "".join([
                child["value"] for child in body_data
                if child["type"] == "rich_text"
            ])
            changed = True

    return page, changed


def pagerevision_to_richtext(revision_data):
    changed = False
    body = revision_data.get("body", "definitely non-JSON string")
    if body:
        try:
            body_data = json.loads(body)
        except ValueError:
            # It's not apparently a StreamField. Leave it.
            pass
        else:
            raw_text = "".join([
                child["value"] for child in body_data
                if child["type"] == "rich_text"
            ])
            revision_data["body"] = raw_text
            changed = True
    return revision_data, changed


def convert(apps, schema_editor, page_converter, pagerevision_converter):
    BlogPage = apps.get_model("demo", "BlogPage")
    content_type = ContentType.objects.get_for_model(BlogPage)
    Revision = apps.get_model("wagtailcore", "Revision")

    for page in BlogPage.objects.all():

        page, changed = page_converter(page)
        if changed:
            page.save()

        for revision in Revision.objects.filter(
            content_type_id=content_type.pk, object_id=page.pk
        ):
            revision_data = revision.content
            revision_data, changed = pagerevision_converter(revision_data)
            if changed:
                revision.content = revision_data
                revision.save()


def convert_to_streamfield(apps, schema_editor):
    return convert(apps, schema_editor, page_to_streamfield, pagerevision_to_streamfield)


def convert_to_richtext(apps, schema_editor):
    return convert(apps, schema_editor, page_to_richtext, pagerevision_to_richtext)


class Migration(migrations.Migration):

    dependencies = [
        # leave the dependency line from the generated migration intact!
        ("demo", "0001_initial"),
        ("wagtailcore", "0076_modellogentry_revision"),
    ]

    operations = [
        migrations.RunPython(
            convert_to_streamfield,
            convert_to_richtext,
        ),

        # leave the generated AlterField intact!
        migrations.AlterField(
            model_name="BlogPage",
            name="body",
            field=wagtail.fields.StreamField(
                [("rich_text", wagtail.blocks.RichTextBlock())],
            ),
        ),
    ]
```

(streamfield_data_migrations)=

## StreamField data migrations

Wagtail provides a set of utilities for creating data migrations on StreamField data. These are exposed through the modules:

-   `wagtail.blocks.migrations.migrate_operation`
-   `wagtail.blocks.migrations.operations`
-   `wagtail.blocks.migrations.utils`

```{note}
   An add-on package [wagtail-streamfield-migration-toolkit](https://github.com/wagtail/wagtail-streamfield-migration-toolkit) is available, additionally providing limited support for auto-generating migrations.
```

### Why are data migrations necessary?

If you change the block definition of a StreamField on a model that has existing data, you may have to manually alter that data to match the new format.

A StreamField is stored as a single column of JSON data in the database. Blocks are stored as structures within the JSON, and can be nested. However, as far as Django is concerned when generating schema migrations, everything inside this column is just a string of JSON data. The database schema doesn’t change - regardless of the content/structure of the StreamField - since it is the same field type before and after any change to the StreamField's blocks. Therefore whenever changes are made to StreamFields, any existing data must be changed into the new required structure, typically by defining a data migration. If the data is not migrated, even a simple change like renaming a block can result in old data being lost.

Generally, data migrations are performed manually by making an empty migration file and writing the forward and backward functions for a `RunPython` command. These functions handle the logic for taking the previously saved JSON representation and converting it into the new JSON representation needed. While this is fairly straightforward for simple changes (such as renaming a block), this can easily get very complicated when nested blocks, multiple fields, and revisions are involved.

To reduce boilerplate, and the potential for errors, `wagtail.blocks.migrations` provides the following:

-   utilities to recurse through stream data structures and apply changes; and
-   operations for common use cases like renaming, removing and altering values of blocks.

(streamfield_migration_basic_usage)=

### Basic usage

Suppose we have a `BlogPage` model in an app named `blog`, defined as follows:

```python
class BlogPage(Page):
    content = StreamField([
        ("stream1", blocks.StreamBlock([
            ("field1", blocks.CharBlock())
        ])),
    ])
```

After running the initial migrations and populating the database with some records, we decide to rename `field1` to `block1`.

```python
class BlogPage(Page):
    content = StreamField([
        ("stream1", blocks.StreamBlock([
            ("block1", blocks.CharBlock())
        ])),
    ])
```

Even though we changed the name to `block1` in our `StreamField` definition, the actual data in the database will not reflect this. To update existing data, we need to create a data migration.

First we create an empty migration file within the app. We can use Django's `makemigrations` command for this:

```sh
python manage.py makemigrations --empty blog
```

which will generate an empty migration file which looks like this:

```python
# Generated by Django 4.0.3 on 2022-09-09 21:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [...]

    operations = [
    ]
```

We need to make sure that either this migration or one of the migrations it depends on has the Wagtail core migrations as a dependency, since the utilities need the migrations for the `Revision` models to be able to run.

```python
    dependencies = [
        ('wagtailcore', '0069_log_entry_jsonfield'),
        ...
    ]
```

(if the project started off with Wagtail 4, '0076_modellogentry_revision' would also be fine)

Next we need a migration operation which Django will run to make our changes. If we weren't using the provided utilities, we would use a `migrations.RunPython` operation, and we would define what data (model, field etc.) we want and how we want to change that data in its forward (function) argument.

Instead, we have a `migrate_operation.MigrateStreamData` operation which will handle accessing the relevant data for us. We need to specify the app name, model name and field name for the relevant StreamField as shown below.

```python
from django.db import migrations

from wagtail.blocks.migrations.migrate_operation import MigrateStreamData

class Migration(migrations.Migration):

    dependencies = [...]

    operations = [
        MigrateStreamData(
            app_name="blog",
            model_name="BlogPage",
            field_name="content",
            operations_and_block_paths=[...]
        ),
    ]
```

In a StreamField, accessing just the field is not enough, since we will typically need to operate on specific block types. For this, we define a block path which points to that specific block path within the `StreamField` definition to obtain the specific data we need. Finally, we define an operation to update that data. As such we have an `(IntraFieldOperation(), 'block_path')` tuple. We can have as many as these as we like in our `operations_and_block_paths`, but for now we'll look at a single one for our rename operation.

In this case the block that we are operating on is `stream1`, the parent of the block being renamed (refer to [](rename_stream_children_operation) - for rename and remove operations we always operate on the parent block). In that case our block path will be `stream1`. Next we need a function that will update our data. For this, the `wagtail.blocks.operations` module has a set of commonly used intra-field operations available (and it is possible to write [custom operations](custom_streamfield_migration_operations)). Since this is a rename operation that operates on a StreamField, we will use `wagtail.blocks.operations.RenameStreamChildrenOperation` which accepts two arguments as the old block name and the new block name. As such our operation and block path tuple will look like this:

```python
(RenameStreamChildrenOperation(old_name="field1", new_name="block1"), "stream1")
```

And our final code will be:

```python
from django.db import migrations

from wagtail.blocks.migrations.migrate_operation import MigrateStreamData
from wagtail.blocks.migrations.operations import RenameStreamChildrenOperation

class Migration(migrations.Migration):

    dependencies = [
        ...
    ]

    operations = [
        MigrateStreamData(
            app_name="blog",
            model_name="BlogPage",
            field_name="content",
            operations_and_block_paths=[
                (RenameStreamChildrenOperation(old_name="field1", new_name="block1"), "stream1"),
            ]
        ),
    ]

```

(using_streamfield_migration_block_paths)=

### Using operations and block paths properly

The `MigrateStreamData` class takes a list of operations and corresponding block paths as a parameter `operations_and_block_paths`. Each operation in the list will be applied to all blocks that match the corresponding block path.

```python
operations_and_block_paths=[
    (operation1, block_path1),
    (operation2, block_path2),
    ...
]
```

#### Block path

The block path is a `'.'`-separated list of names of the block types from the top level `StreamBlock` (the container of all the blocks in the StreamField) to the nested block type which will be matched and passed to the operation.

```{note}
If we want to operate directly on the top level `StreamBlock`, then the block path must be
an empty string `""`.
```

For example, if our stream definition looks like this:

```python
class MyDeepNestedBlock(StreamBlock):
    foo = CharBlock()
    date = DateBlock()

class MyNestedBlock(StreamBlock):
    char1 = CharBlock()
    deepnested1 = MyDeepNestedBlock()

class MyStreamBlock(StreamBlock):
    field1 = CharBlock()
    nested1 = MyNestedBlock()

class MyPage(Page):
    content = StreamField(MyStreamBlock)
```

If we want to match all "field1" blocks, our block path will be `"field1"`:

```python
[
    { "type": "field1", ... }, # this is matched
    { "type": "field1", ... }, # this is matched
    { "type": "nested1", "value": [...] },
    { "type": "nested1", "value": [...] },
    ...
]
```

If we want to match all "deepnested1" blocks, which are a direct child of "nested1", our block path will be `"nested1.deepnested1"`:

```python
[
    { "type": "field1", ... },
    { "type": "field1", ... },
    { "type": "nested1", "value": [
        { "type": "char1", ... },
        { "type": "deepnested1", ... }, # This is matched
        { "type": "deepnested1", ... }, # This is matched
        ...
    ] },
    { "type": "nested1", "value": [
        { "type": "char1", ... },
        { "type": "deepnested1", ... }, # This is matched
        ...
    ] },
    ...
]
```

When the path contains a ListBlock child, 'item' must be added to the block path as the name of said child. For example, if we consider the following stream definition:

```python
class MyStructBlock(StructBlock):
    char1 = CharBlock()
    char2 = CharBlock()

class MyStreamBlock(StreamBlock):
    list1 = ListBlock(MyStructBlock())
```

Then if we want to match "char1", which is a child of the StructBlock which is the direct list child, we have to use `block_path_str="list1.item.char1"` instead of `block_path_str="list1.char1"`. We can also match the `ListBlock` child with `block_path_str="list1.item"`.

#### Rename and remove operations

The following operations are available for renaming and removing blocks.

-   [RenameStreamChildrenOperation](rename_stream_children_operation)
-   [RenameStructChildrenOperation](rename_struct_children_operation)
-   [RemoveStreamChildrenOperation](remove_stream_children_operation)
-   [RemoveStructChildrenOperation](remove_struct_children_operation)

Note that all of these operations operate on the value of the parent block of the block which must be removed or renamed. Hence make sure that the block path you are passing points to the parent block when using these operations (see the example in [basic usage](streamfield_migration_basic_usage)).

#### Alter block structure operations

The following operations allow you to alter the structure of blocks in certain ways.

-   [](stream_children_to_list_block_operation): operates on the value of a `StreamBlock`. Combines all child blocks of type `block_name` as children of a single ListBLock which is a child of the parent `StreamBlock`.
-   [](stream_children_to_stream_block_operation): operates on the value of a `StreamBlock`. Note that `block_names` here is a list of block types and not a single block type unlike `block_name` in the previous operation. Combines each child block of a type in `block_names` as children of a single `StreamBlock` which is a child of the parent `StreamBlock`.
-   [](stream_children_to_struct_block_operation): moves each `StreamBlock` child of the given type inside a new `StructBlock`

A new `StructBlock` will be created as a child of the parent `StreamBlock` for each child block of the given type, and then that child block will be moved from the parent `StreamBlock`'s children inside the new `StructBlock` as a child of that `StructBlock`.

For example, consider the following `StreamField` definition:

```python
mystream = StreamField([("char1", CharBlock()) ...], ...)
```

Then the stream data would look like the following:

```python
[
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
    ...
    { "type": "struct1", "value": { "char1": "Value1" } },
    { "type": "struct1", "value": { "char1": "Value2" } },
    ...
]
```

```{note}
Block ids are not preserved here since the new blocks are structurally different than the previous blocks.
```

#### Other operations

-   [](alter_block_value_operation)

(custom_streamfield_migration_operations)=

### Making custom operations

#### Basic usage

While this package comes with a set of operations for common use cases, there may be many instances where you need to define your own operation for mapping data. Making a custom operation is fairly straightforward. All you need to do is extend the `BaseBlockOperation` class and define the required methods,

-   `apply`  
    This applies the actual changes to the existing block value and returns the new block value.
-   `operation_name_fragment`  
    (`@property`) Returns a name to be used for generating migration names.

(**NOTE:** `BaseBlockOperation` inherits from `abc.ABC`, so all of the required methods
mentioned above have to be defined on any class inheriting from it.)

For example, if we want to truncate the string in a `CharBlock` to a given length,

```python
from wagtail.blocks.migrations.operations import BaseBlockOperation

class MyBlockOperation(BaseBlockOperation):
    def __init__(self, length):
        super().__init__()
        # we will need to keep the length as an attribute of the operation
        self.length = length

    def apply(self, block_value):
        # block value is the string value of the CharBlock
        new_block_value = block_value[:self.length]
        return new_block_value


    @property
    def operation_name_fragment(self):
        return "truncate_{}".format(self.length)

```

#### block_value

Note that depending on the type of block we're dealing with, the `block_value` which is passed to `apply` may take different structures.

For non-structural blocks, the value of the block will be passed directly. For example, if we're dealing with a `CharBlock`, it will be a string value.

The value passed to `apply` when the matched block is a StreamBlock would look like this,

```python
[
    { "type": "...", "value": "...", "id": "..." },
    { "type": "...", "value": "...", "id": "..." },
    ...
]
```

The value passed to `apply` when the matched block is a StructBlock would look like this,

```python
{
    "type1": "...",
    "type2": "...",
    ...
}
```

The value passed to `apply` when the matched block is a ListBlock would look like this,

```python
[
    { "type": "item", "value": "...", "id": "..." },
    { "type": "item", "value": "...", "id": "..." },
    ...
]
```

#### Making structural changes

When making changes involving the structure of blocks (changing the block type for example), it may be necessary to operate on the block value of the parent block instead of the block to which the change is made, since only the value of a block is changed by the `apply` operation.

Take a look at the implementation of `RenameStreamChildrenOperation` for an example.

#### Old list format

Prior to Wagtail version 2.16, `ListBlock` children were saved as just a normal Python list of values. However, for newer versions of Wagtail, list block children are saved as `ListValue`s. When handling raw data, the changes would look like the following:

Old format

```python
[
    value1,
    value2,
    ...
]
```

New format

```python
[
    { "type": "item", "id": "...", "value": value1 },
    { "type": "item", "id": "...", "value": value2 },
    ...
]
```

When defining an operation that operates on a ListBlock value, in case you have old data which is still in the old format, it is possible to use `wagtail.blocks.migrations.utils.formatted_list_child_generator` to obtain the children in the new format like so:

```python
    def apply(self, block_value):
        for child_block in formatted_list_child_generator(list_block_value):
            ...
```
