(api_v3_streamfield)=

# StreamField and relations in the API

[StreamField](streamfield_topic) content is written and read through the v3 API as a list of blocks. The API supports the full range of StreamField behaviour: nested blocks, chooser values, rich text inside blocks, and writable child relations behind `InlinePanel` / `ParentalKey`. Rich text inside blocks follows the formats on this page, with the rich text input caveats described in [](api_v3_rich_text). This page is the reference for how StreamField values are represented and how they are written in the API.

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
-   **TableBlock** — an object with the following properties:
    -   `data` (a list of rows, each a list of cell strings or `null`)
    -   `table_header_choice` (`row`, `column`, `both`, or `neither`)
    -   `first_row_is_table_header`
    -   `first_col_is_header`
    -   `table_caption` (optional)
    -   `cell` (cell metadata such as `className`)
    -   `mergeCells`

    On input, `first_row_is_table_header` and `first_col_is_header` are derived from `table_header_choice`.
-   **TypedTableBlock** — an object with the following properties:
    -  `columns` (each with a `type` and a `heading`)
    -  `rows` (each with a `values` list holding one value per column, in that column block's own representation)
    -  `caption`
-   **Chooser and leaf blocks** (for example image and page choosers) — a scalar value such as the object's ID, or another widget-compatible value.

Custom blocks can customise how they are read back through the API by [defining `get_api_representation()`](apiv2_streamfield_configuration), which takes precedence over the default representation.

The representation reflected in the OpenAPI schema is for documentation only. Values are not validated or serialized against it. A block is described as "any" value if its shape isn't known, such as a custom block not based on a built-in block, or one that overrides `to_python` or `get_prep_value` (or `get_api_representation`, for the read schema).

## Writing StreamField values

StreamField values are submitted as part of a page or snippet create or update, using the representation above. The following semantics apply:

-   Block IDs are optional on input. The `id` will be used if provided, otherwise it will be automatically generated.
-   Updating a page (a `PATCH` that includes the StreamField field) replaces the whole field value with what you submit.
    -   This is not block-level patching: any blocks you omit are removed. To add, change, or remove individual blocks, submit the complete desired list.
-   Omitting the StreamField from an update leaves it unchanged.
-   An unknown block type in the submitted list returns `422`.
-   Values are validated by the block's form widget and `clean()` method.

Built-in blocks do not need any extra code to be writable, and nor do custom blocks based on `StreamBlock`, `ListBlock`, `StructBlock`, or `FieldBlock` (including chooser blocks).

A submitted value takes the same shape as the block's stored value, which for built-in blocks is also their default API representation. Writes don't use a custom `get_api_representation()`, so a block that overrides it still accepts the stored shape on input.

Each field block's value is passed through its form widget and validated by the block's `clean()` method. Rich text is also converted from any accepted rich text input format.

A custom block that contains other blocks but isn't based on `StreamBlock`, `ListBlock`, or `StructBlock` must define `map_child_values(value, func)` to be writable, returning its stored value with `func(child_block, child_value, child_path)` applied to each child value, so its children are handled in the same way. See `TypedTableBlock` for an example. Writing any other kind of custom block returns `422`.

```{note}
Because updating replaces the whole value, build clients that send the complete StreamField list for the field rather than relying on partial, block-level updates.
```

(api_v3_child_relations)=

## Child relations

Inline model relationships are exposed as a list of children within the parent's payload. [Similar to `InlinePanel`](inline_models), this can be done by adding an `APIField` that points to the `related_name` of the `ParentalKey`.

When the relation and its child fields are writable, these follow the same replace-as-a-whole rules as StreamField values. When you supply a child relation on update:

-   existing children whose primary key matches are edited in place, so an item read from the API can be sent back as-is;
-   existing children you omit from the list are deleted when the relation is supplied;
-   children with unmatched or missing primary keys are created;
-   for an orderable child model, the children are saved in the order they're submitted;
-   omitting the relation entirely leaves it untouched.

Each submitted child item replaces that child's writable fields as a whole: a field you omit from an item is treated as empty, not left unchanged. Include all of an item's fields when editing it.

### Nested child relations

A child model can have child relations of its own, similar to an `InlinePanel` defined on an `InlinePanel` child model. When listed in the child model's `api_fields`, these are included within each child item, and are written using the same rules, against that child's own existing children:

-   omitting a nested relation from an item leaves that child's existing nested children untouched, and gives a new child none;
-   supplying an empty list removes them;
-   deleting a child also deletes its nested children.

Other reverse relations are only included at the top level of a page or snippet, not within child items.

## Example: create a page with a StreamField

This example creates a blog page whose body contains a heading, a paragraph, and an image chooser. It assumes a `BASE` pointing at the mounted API, a bearer `TOKEN`, and an existing image with ID `42`.

Submit the StreamField value as a list, one entry per block:

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
