(api_v3_rich_text)=

# Rich text in the API

Rich text fields are stored in Wagtail's database HTML format, described in [](rich_text_internals), and the v3 API uses that format as its rich text interchange representation.

## Output formats

Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of [`WAGTAILAPI_RICH_TEXT_FORMAT`](wagtailapi_settings):

- `db_html` (default): Wagtail's [internal storage format](rich_text_internals).
- `html`: display-ready HTML, converted like in templates.
- `db_markdown`: Markdown that preserves internal references as `wagtail://` URLs, similarly to `db_html`.
- `markdown`: Markdown with references resolved to public URLs (page URLs, image rendition URLs), like `html`. Line breaks are output as hard line breaks (a backslash at the end of the line), whereas `db_markdown` keeps them as plain newlines so that it can be converted back to database HTML without loss.

## Input formats

On writes, a rich text field value (including a `RichTextBlock` value in a StreamField) accepts either a plain string (database HTML) or an envelope object:

```json
"body": {"format": "db_markdown", "content": "# Title\n\n[about](wagtail://page?id=3)"}
```

Supported input formats:

- `db_html`: database HTML (the default when `format` is omitted).
- `db_markdown`: Markdown using the `wagtail://` reference syntax.

Input is sanitized against the field's or block's features. Elements that are removed or unwrapped as a result are reported in the response's `meta.warnings`, for example:

```json
"meta": {
  "type": "...",
  "warnings": [
    {
      "tag": "h2",
      "action": "unwrapped",
      "reason": "feature_disabled",
      "attribute": null,
      "detail": "<h2>T</h2>"
    }
  ]
}
```

The `reason` value is one of `feature_disabled`, `unknown_linktype`, `unknown_embedtype` or `missing_attribute`. Only element-level changes are reported: attributes stripped from an allowed element are not. The `detail` value is a truncated excerpt of the submitted markup and should be treated as untrusted.
