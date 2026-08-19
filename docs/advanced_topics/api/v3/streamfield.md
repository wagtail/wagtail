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
-   **ListBlock** — a plain list of the child block's values, without per-item `type` or `id`.
-   **StructBlock** — an object keyed by the child block's field names.
-   **RichTextBlock** — rich text, using the input and output formats described in [](api_v3_rich_text).
-   **Chooser and leaf blocks** (for example image and page choosers) — a scalar value such as the object's ID, or another widget-compatible value.

Custom blocks can customise how they are read back through the API by defining `get_api_representation()`, which takes precedence over the default representation.

## Writing StreamField values

StreamField values are submitted as part of a page or snippet create or update, using the representation above. The following semantics apply:

-   **Block IDs** are optional on input. When a block's `id` is omitted, Wagtail generates one; when you supply an `id`, it is preserved as given.
-   **Updating a page** (a `PATCH` that includes the StreamField field) replaces the whole field value with what you submit. This is not block-level patching: any blocks you omit are removed. To add, change, or remove individual blocks, submit the complete desired list.
-   Omitting the StreamField field from an update leaves it unchanged.
-   An **unknown block type** in the submitted list returns `422`.
-   Values are validated by the block's real `clean()` method and the form widget, and chooser IDs are validated, so the same validation applies as in the editor.

```{note}
Because updating replaces the whole value, build clients that send the complete StreamField list for the field rather than relying on partial, block-level updates.
```

## Child relations

Writable relationships defined with `InlinePanel` on a `ParentalKey` are exposed as a list of generated child schemas within the parent's payload. These follow the same replace-as-a-whole rules as StreamField values. When you supply a child relation on update:

-   existing children whose `id` matches are edited in place;
-   existing children you omit from the list are deleted when the relation is supplied;
-   children with unmatched or missing IDs are created;
-   omitting the relation entirely leaves it untouched.

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
