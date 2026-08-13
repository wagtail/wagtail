(api_v3)=

# Wagtail API v3

Wagtail 8.0 introduces a v3 API built on [Django Ninja](https://django-ninja.dev/) and [Pydantic](https://docs.pydantic.dev/). It provides OpenAPI 3.1 schema export and declarative per-type schemas to support read and write CMS operations described in [RFC 115](https://wagtail.org/rfc-115/).

The v2 read API remains available. v3 is mounted separately at `/api/v3/`.

```{toctree}
---
maxdepth: 1
---
authentication
reference
```

## Quick start

Register the API URLs in your project:

```python
# urls.py
from wagtail.api.v3.urls import api

urlpatterns = [
    path("api/v3/", api.urls),
]
```

Browse the interactive docs at `/api/v3/docs` and the OpenAPI schema at `/api/v3/openapi.json`.

The v3 API reads the same `WAGTAILAPI_*` settings as v2 where applicable (`WAGTAILAPI_BASE_URL`, `WAGTAILAPI_LIMIT_MAX`, `WAGTAILAPI_SEARCH_ENABLED`, `WAGTAILAPI_RICH_TEXT_FORMAT`). See [](api_v2_configuration) and the [API settings reference](wagtailapi_settings).

## Pagination

List endpoints use Django Ninja's limit/offset pagination:

```json
{
    "count": 42,
    "items": []
}
```

`count` is the total number of results irrespective of pagination. Use `?limit` and `?offset` query parameters to page through results. `WAGTAILAPI_LIMIT_MAX` caps the maximum `limit` value (see [](api_v2_configuration) and the [API settings reference](wagtailapi_settings)).

## Rich text

Rich text fields are stored in Wagtail's database HTML format, described in [](rich_text_internals), and the v3 API uses that format as its rich text interchange representation.

### Input formats

On writes, a rich text field value accepts either a plain string (database HTML, sanitised against the field's declared features) or an envelope object:

```json
"body": {"format": "db_markdown", "content": "# Title\n\n[about](wagtail://page?id=3)"}
```

Supported input formats:

- `db_html`: database HTML (the default when `format` is omitted).
- `db_markdown`: Markdown using the `wagtail://` reference syntax described below.

Markdown input is converted to database HTML and sanitised against the field's features exactly like `db_html` input: out-of-feature constructs are stripped. Malformed `wagtail://` references — an unparsable `id`, or a page/document reference missing its `id` — fail the request with a 422 validation error naming the field and Markdown line. Media references missing a `url`, and image references missing a `format`, are dropped during sanitisation instead, never stored verbatim — the reference syntax table below lists which parameters are required.

### Output formats

Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of `WAGTAILAPI_RICH_TEXT_FORMAT`:

- `db_html` (default): Wagtail's database HTML, with internal references by id (`<a linktype="page" id="3">`).
- `html`: display-ready HTML, via `expand_db_html` (page references expanded to URLs).
- `db_markdown`: Markdown that preserves internal references as `wagtail://` URLs — the format to round-trip through.
- `markdown`: Markdown with references resolved to public URLs (page URLs, image rendition URLs) — the Markdown analogue of `html`. Dangling page or document references degrade to plain text.

Markdown output is normalised to exactly one trailing blank line, and is parameterised by the field's features, matching the database HTML the editor would produce for that field.

Markdown support is **experimental** (the underlying draftjs_exporter library marks it experimental) and requires `draftjs_exporter>=7.0.0,<8.0`.

### Reference syntax

Internal object references travel in Markdown as `wagtail://` URLs in link and image destinations:

| Markdown | Resolves to |
| --- | --- |
| `[text](wagtail://page?id=3)` | page 3 |
| `[text](wagtail://document?id=5)` | document 5 |
| `![alt](wagtail://image?id=42&format=left)` | image 42, `left` format, alt text from the label |
| `![label](wagtail://media?url=https%3A%2F%2Fyoutu.be%2Fabc)` | media embed with percent-encoded URL (label is informative only) |

`id` is required for page, document, and image references; `format` (an image format name such as `left`, `right`, or `fullwidth`) is required for image references; `url` is required for media references. Empty values count as missing: `wagtail://image?id=42&format=` is treated like a missing `format`. Missing `id` on a page or document reference is a 422 validation error; a missing `format` or `url` drops the embed during sanitisation.

Round-tripping `db_markdown` through the API preserves these references exactly, including references to objects that no longer exist.

### Supported Markdown subset and lossy conversions

Markdown input covers the CommonMark core: ATX headings, blockquotes, fenced code blocks, thematic breaks, ordered/unordered lists, bold/italic/inline code, inline links and images, and hard line breaks. Inline `<sup>`/`<sub>` HTML tags are the only interpreted HTML, imported as superscript/subscript; all other raw HTML becomes literal text — it can never bypass sanitisation. Unsupported constructs (reference-style links, Setext headings, tables, indented code blocks, list item continuation lines, autolinks) are treated as plain text.

Known lossy conversions:

- Strikethrough is emitted as `~~text~~` on output but not re-imported (leaves literal tildes).
- Styles with no Markdown syntax (underline, mark) degrade to plain text on output; superscript/subscript output as inline `<sup>`/`<sub>` HTML and re-import only when the field declares those features.
- Resolved `markdown` output loses internal identifiers by design; dangling page/document links become plain text, dangling images keep their `wagtail://` reference.
- Media embeds output as an image reference (`db_markdown`) or a block-level `[label](url)` link (resolved `markdown`).

## Error format

All error responses use [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) `application/problem+json`:

```json
{
    "type": "https://docs.wagtail.org/api/v3/validation-error",
    "title": "Unprocessable Entity",
    "status": 422,
    "detail": "Validation failed",
    "errors": []
}
```

## Images

Images are available at `/api/v3/images/`:

- `GET /images/`: list images. Anonymous access, excluding images in restricted collections. Supports `?search=`, `?order=`, and filtering on the image's own fields (`title`, `width`, `height`, plus any `api_fields` the project declares) via query parameters.
- `GET /images/{id}/`: image detail.
- `POST /images/`: create an image. This endpoint uses `multipart/form-data`: the `file` field carries the image binary, and writable metadata (title, description, collection, focal point) is sent as individual form fields.
- `PATCH /images/{id}/`: update the same writable metadata as JSON. Does not support changing the image file itself.

Tags are returned in image responses under `meta.tags`, but are not writable through the images API yet.
- `DELETE /images/{id}/`: delete an image.

Image writes enforce the same validation (max upload size, max pixels, extensions) and collection permissions as the admin.

### Image renditions

Renditions are exposed per-project through `api_fields`, the same mechanism as [in the v2 API](api_v2_images):

```python
from wagtail.images.api.fields import ImageRenditionField


class BlogPage(Page):
    ...

    api_fields = [
        APIField("thumbnail", serializer=ImageRenditionField("fill-300x300")),
    ]
```

## Documents

Documents are available at `/api/v3/documents/`. The routes are flat rather than nested under collections:

- `GET /documents/`: list documents. Anonymous access, excluding documents whose direct collection has an unpassed view restriction. Supports `?search=`, `?order=`, and field filtering.
- `GET /documents/{id}/`: document detail. Anonymous access, with the same direct-collection restriction behavior as the list endpoint.
- `POST /documents/`: create a document using `multipart/form-data`. Both `file` (the binary) and `title` are required; send other writable metadata such as `collection_id` as individual form fields.
- `PATCH /documents/{id}/`: update writable metadata as JSON. The document file cannot be replaced through this endpoint.
- `DELETE /documents/{id}/`: delete a document.

Document uploads enforce `WAGTAILDOCS_EXTENSIONS`, `WAGTAILDOCS_MAX_UPLOAD_SIZE`, custom form validation, and collection permissions in the same way as admin uploads. Extension validation checks the filename and does not verify that the file contents match the extension; see [](user_uploaded_files) for guidance on handling untrusted uploads.
