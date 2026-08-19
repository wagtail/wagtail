(api_v3_rich_text)=

# Rich text in the API

Rich text fields are stored in Wagtail's database HTML format, described in [](rich_text_internals), and the v3 API uses that format as its rich text interchange representation.

## Output formats

Rich text fields use the `?rich_text_format=` query parameter, which supports the same options as the project-level default of [`WAGTAILAPI_RICH_TEXT_FORMAT`](wagtailapi_settings):

- `db_html` (default): Wagtail's [internal storage format](rich_text_internals).
- `html`: display-ready HTML, converted like in templates.
- `db_markdown`: Markdown that preserves internal references as `wagtail://` URLs, similarly to `db_html`.
- `markdown`: Markdown with references resolved to public URLs (page URLs, image rendition URLs), like `html`.

## Input formats

On writes, a top-level page rich text field value accepts either a plain string (database HTML, sanitised against the field's declared features) or an envelope object:

```json
"body": {"format": "db_markdown", "content": "# Title\n\n[about](wagtail://page?id=3)"}
```

Supported input formats:

- `db_html`: database HTML (the default when `format` is omitted).
- `db_markdown`: Markdown using the `wagtail://` reference syntax described below.

Markdown input is converted and sanitized for storage as database HTML.

```{note}
These string and envelope input formats are guaranteed for top-level page rich text fields. Rich text fields on other models (for example snippets) do not currently share the same input conversion path, so treat string and envelope input there as unsupported.
```

Sanitization removes content that is not allowed by the field's features, and these removals are not reported back to the caller: a response can silently contain less than what was submitted.
