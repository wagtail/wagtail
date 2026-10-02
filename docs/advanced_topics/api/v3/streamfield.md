(api_v3_streamfield)=

# StreamField and relations in the API

[StreamField](streamfield_topic) content is written and read through the v3 API as an internal-style list of blocks. The API supports the full range of StreamField behaviour: nested blocks, chooser values, rich text inside blocks, and writable child relations behind `InlinePanel` / `ParentalKey`. Rich text inside blocks follows the formats on this page, with the rich text input caveats described in [](api_v3_rich_text). This page is the reference for how StreamField values are represented and how they are written.

A StreamField value on a page or snippet maps to an array of blocks, each with a `type`, an `id`, and a `value`. The `value` shape depends on the block type, as described below.

## Representation

A top-level StreamBlock value is a JSON array of blocks:

```json
[
    {
        "type": "heading",
        "id": "0e3b2f5c-4d1a-4f2b-9c8e-7b6a2f40d1e2",
        "value": "Example"
    },
    {
        "type": "paragraph",
        "id": "0e3b2f5c-4d1a-4f2b-9c8e-7b6a2f40d1e3",
        "value": "A paragraph of text."
    },
    {
        "type": "image",
        "id": "0e3b2f5c-4d1a-4f2b-9c8e-7b6a2f40d1e4",
        "value": 42
    }
]
```

The `value` representation depends on the block type:

-   **Nested StreamBlock** — a list of `{type, id, value}` blocks, recursively.
-   **ListBlock** — a plain list of the child block's values, without per-item `type` or `id`. On input, an item can also be given as `{"type": "item", "id": ..., "value": ...}`, which keeps its `id`.
-   **StructBlock** — an object keyed by the child block's field names.
-   **RichTextBlock** — rich text, using the input and output formats described in [](api_v3_rich_text).
-   **TypedTableBlock** — an object with `columns` (each with a `type` and a `heading`), `rows` (each with a `values` list holding one value per column, in that column block's own representation), and a `caption`.
-   **Chooser and leaf blocks** (for example image and page choosers) — a scalar value such as the object's ID, or another widget-compatible value.

Custom blocks can customise how they are read back through the API by [defining `get_api_representation(value, context=None)`](apiv2_streamfield_configuration), which takes precedence over the default representation.

## Writing StreamField values

StreamField values are submitted as part of a page or snippet create or update, using the representation above. The following semantics apply:

-   **Block IDs** are optional on input. When a block's `id` is omitted, Wagtail generates one; when you supply an `id`, it is preserved as given.
-   **Updating a page** (a `PATCH` that includes the StreamField field) replaces the whole field value with what you submit. This is not block-level patching: any blocks you omit are removed. To add, change, or remove individual blocks, submit the complete desired list.
-   Omitting the StreamField field from an update leaves it unchanged.
-   An **unknown block type** in the submitted list returns `422`.
-   Values are validated by the block's real `clean()` method and the form widget, and chooser IDs are validated, so the same validation applies as in the editor.

Built-in blocks need no extra code to be writable, and nor do custom blocks based on `StreamBlock`, `ListBlock`, `StructBlock`, or `FieldBlock` (including chooser blocks). A submitted value takes the same shape as the block's stored value, which for built-in blocks is also their default API representation. Writes don't use a custom `get_api_representation`, so a block that overrides it still accepts the stored shape on input. Each field block's value is passed through its form widget, as when submitted through the editor, and the whole value is validated by the blocks' `clean()` methods. Rich text is also converted from any accepted rich text input format. A custom block that contains other blocks but isn't based on `StreamBlock`, `ListBlock`, or `StructBlock` must define `map_child_values(value, func)` to be writable, returning its stored value with `func(child_block, child_value, child_path)` applied to each child value, so its children are handled in the same way. See `TypedTableBlock` for an example. Writing any other kind of custom block returns `422`.

```{note}
Because updating replaces the whole value, build clients that send the complete StreamField list for the field rather than relying on partial, block-level updates.
```

(api_v3_child_relations)=

## Child relations

Writable relationships defined with `InlinePanel` on a `ParentalKey` are exposed as a list of generated child schemas within the parent's payload. A relation is named by its accessor on the parent model: the `related_name` of the `ParentalKey`, or the default `<model name>_set` if it has none. When you supply a child relation on update:

-   the relation's children are set to the list you submit. For an orderable child model, they are stored in the submitted order;
-   an existing child is matched by its primary key, under the primary key field's name as returned when reading it (usually `id`, or e.g. `custom_id` for a model with a custom primary key), so an item read from the API can be sent back as-is;
-   a matched child is updated with the fields you supply, and keeps the current values of the fields you omit. To clear a field, supply an empty value;
-   children with unmatched or missing primary keys are created;
-   existing children you omit from the list are deleted;
-   omitting the relation entirely leaves it untouched.

As in the editor, required fields are only enforced when publishing, unless they can't be stored empty, such as a non-nullable foreign key. A new child with every field empty is ignored, unless the child model is orderable: its position in the list counts as a value, so it's created, or rejected if it fails validation.

### Nested child relations

A child model can have child relations of its own, such as an `InlinePanel` within an `InlinePanel` child. When listed in the child model's `api_fields`, these are included within each child item, and are written using the same rules, against that child's own existing children:

-   omitting a nested relation from an item leaves that child's existing nested children untouched, and gives a new child none;
-   supplying an empty list removes them;
-   deleting a child also deletes its nested children.

Other reverse relations are only included at the top level of a page or snippet, not within child items.

StreamField values nested inside child forms use the same flattening path as top-level StreamField fields.

## Schema discovery limitation

Although the v3 API reads and writes StreamField content fully at runtime, the generated OpenAPI schema represents a StreamField as `list[Any]`. There is currently no per-block JSON Schema and no `/schema/blocks/` endpoint, so the OpenAPI schema alone cannot tell a client which block types are required, what properties a `StructBlock` has, what list items a `ListBlock` accepts, which objects a chooser targets, or which rich text features a block allows. For practical discovery, rely on the page's own schema for the field's existence along with this reference, and see the [schema discovery guide](api_v3_schema) for how per-type schemas are generated.

## Example: create a page with a StreamField

This example creates a blog page whose body contains a heading, a paragraph, and an image chooser. It assumes a `BASE` pointing at the mounted API, a bearer `TOKEN`, and an existing image with ID `42`.

Submit the StreamField value as the internal-style list, one entry per block:

```sh
curl -X POST "$BASE/pages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"type": "blog.BlogPage", "parent_id": 3},
    "title": "Example",
    "body": [
      {"type": "heading", "id": "0e3b2f5c-0000-0000-0000-000000000001", "value": "Example"},
      {"type": "paragraph", "id": "0e3b2f5c-0000-0000-0000-000000000002", "value": "A paragraph of text."},
      {"type": "image", "id": "0e3b2f5c-0000-0000-0000-000000000003", "value": 42}
    ]
  }'
```

Each block supplies a stable `id` you control, so a later update can resubmit the same blocks with their IDs. If you prefer, omit the `id` fields and Wagtail generates them when the page is saved.
