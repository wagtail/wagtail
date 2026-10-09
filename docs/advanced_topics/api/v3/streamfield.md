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

A custom block that is not a `FieldBlock` and reads its own form data in `value_from_datadict` can accept API input by defining `get_api_form_data(value, prefix, flatten_child)`. It receives the submitted value and the block's form prefix, and returns a dictionary of the form data keys its `value_from_datadict` reads. To include the value of a child block, call `flatten_child(child_block, child_value, child_prefix)`, which writes the child's form data in the same way as any other block. `TypedTableBlock` uses this method.

## Writing StreamField values

StreamField values are submitted as part of a page or snippet create or update, using the representation above. The following semantics apply:

-   **Block IDs** are optional on input. When a block's `id` is omitted, Wagtail generates one; when you supply an `id`, it is preserved as given.
-   **Updating a page** (a `PATCH` that includes the StreamField field) sets the field's blocks to the list you submit, in the submitted order. Any blocks you omit are removed.
-   A submitted block whose `id` and `type` match a block in the current value is **merged** with it. Omit its `value` to keep the current value, or omit keys from a StructBlock value to keep the current values of those child blocks. The children of a nested StreamBlock or ListBlock are matched by `id` and merged in the same way. Any other value, such as text, rich text, or a chooser value, replaces the current one as submitted.
-   Omitting the StreamField field from an update leaves it unchanged.
-   An **unknown block type** in the submitted list returns `422`, as does a block without a `value` that does not match a current block.
-   Values are validated by the block's real `clean()` method and the form widget, and chooser IDs are validated, so the same validation applies as in the editor.

```{note}
Merging relies on the block IDs stored with the content, as returned when reading it. Content saved through the editor or the API always stores them. Content written by other means may not, in which case each read returns new IDs and the blocks cannot be matched.
```

(api_v3_child_relations)=

## Child relations

Writable relationships defined with `InlinePanel` on a `ParentalKey` are exposed as a list of generated child schemas within the parent's payload. A relation is named by its accessor on the parent model: the `related_name` of the `ParentalKey`, or the default `<model name>_set` if it has none. When you supply a child relation on update:

-   the relation's children are set to the list you submit. For an orderable child model, they are stored in the submitted order;
-   an existing child is matched by its primary key, under the primary key field's name as returned when reading it (usually `id`);
-   a matched child is updated with the fields you supply, and keeps the current values of the fields you omit. To clear a field, supply an empty value;
-   children with unmatched or missing primary keys are created;
-   existing children you omit from the list are deleted;
-   omitting the relation entirely leaves it untouched.

StreamField values inside a child follow the same writing rules as top-level StreamField values, including merging into a matched child's current value.

A child model can declare its own `InlinePanel`, and that nested relation is written as a list within each child, following the same rules. Omitting a nested relation from a child leaves an existing child's nested children untouched, and gives a new child none. Read responses currently include only one level of child relations, so nested children are not returned.

As in the editor, a new child with every field empty is ignored, and required fields are only enforced when publishing.

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
