(api_v3_rich_text)=

# Rich text and Markdown

Rich text fields in Wagtail are stored in Wagtail's database HTML format, described in [](rich_text_internals). The v3 API uses that as its interchange representation: it accepts rich text input in a couple of formats, converts and sanitises it for storage as database HTML, and can return rich text in any of four output formats. This page is the reference for those formats, the `wagtail://` internal-reference syntax, and the limits of round-tripping rich text through the API.

The same `?rich_text_format=` query parameter applies wherever rich text is returned. The output default is set project-wide by [`WAGTAILAPI_RICH_TEXT_FORMAT`](wagtailapi_settings), which must be one of the four formats below.

## Output formats

Rich text output is selected by the `?rich_text_format=` query parameter, which overrides the project-wide default of `WAGTAILAPI_RICH_TEXT_FORMAT`. The four formats are:

- **`db_html`** (default) — Wagtail's internal database HTML format, as stored.
- **`html`** — display-ready HTML for a public page, converted the same way as in templates.
- **`db_markdown`** — Markdown that preserves internal references as `wagtail://` destinations, so content can be moved between formats without losing links to other Wagtail content. This is the closest to a reference-preserving interchange format.
- **`markdown`** — Markdown with internal references resolved to public URLs (page URLs, image rendition URLs), suitable for consumption by external tools.

```sh
# Return a page's rich text as reference-preserving Markdown
curl "https://example.com/api/v3/pages/3/?rich_text_format=db_markdown"
```

## Input formats

On writes, a top-level page rich text field value accepts either a plain string or an envelope object specifying the format:

```json
"body": {"format": "db_markdown", "content": "# Title\n\n[about](wagtail://page?id=3)"}
```

Supported input formats:

- A **plain string** — interpreted as database HTML.
- **`db_html`** — an explicit envelope declaring database HTML.
- **`db_markdown`** — Markdown using the `wagtail://` reference syntax described below.

`html` and `markdown` are output-only formats; they are not accepted as input.

Input is sanitised against the rich text field's declared feature list using Wagtail's database HTML converter. `db_markdown` input is first converted through Wagtail's content-state conversion and then sanitised against the same feature list. The guaranteed string/envelope input formats (above) apply to top-level page rich text fields. Inside StreamField rich text blocks the same formats are accepted, but with some inconsistencies (see [](api_v3)): an unknown format returns HTTP 400 rather than 422, and block Markdown output is not feature-aware. Top-level rich text fields on other models (for example snippets) do not share the page conversion path.

```{note}
Sanitisation strips content that is not allowed by the field's features, and these removals are not reported back to the caller. A stored or returned value can silently contain less than what was submitted, so validate or strip unsupported content client-side when that matters.
```

## Internal references

Markdown (`db_markdown` input and output, and resolved `markdown` output) uses `wagtail://` destinations to refer to other Wagtail content without hard-coding public URLs. Examples:

- `wagtail://page?id=3` — a page.
- `wagtail://document?id=4` — a document.
- `wagtail://image?id=5&format=...` — an image, optionally with a rendition format.
- Media references — files or other media hosted by Wagtail.

Missing or non-integer required IDs produce validation errors. When a reference cannot be resolved, the resolved `markdown`/`html` output may degrade the link to plain text or to a fallback reference rather than fail.

## Round-trip limitations

Rich text does not round-trip byte-for-byte, and conversion is not fully lossless:

- Feature sanitisation intentionally strips content that is not in the field's feature list.
- Output Markdown is normalised, so the exact Markdown you submit is not guaranteed to come back unchanged.
- Resolved output (`html` and `markdown`) loses internal `wagtail://` identifiers when it expands references to public URLs.
- Dangling references may degrade to plain text or a fallback reference.
- Unsupported styles or tags may be unwrapped, and block or paragraph structure may be normalised as content passes through conversion.

Because `db_markdown` keeps `wagtail://` references intact, it is the recommended format when you need to move content between systems and back without losing links to other Wagtail content. For long-term storage, `db_html` is the format Wagtail stores internally.

## Example: round-trip a rich text field

This example reads a page's `body` rich text field as `db_markdown`, edits it, writes it back with the `db_markdown` input envelope, then reads it again as `html` for a public site front-end. It assumes a `BASE` pointing at the mounted API and a bearer `TOKEN` for the write.

First, read the current value as reference-preserving Markdown. This keeps `wagtail://` references to other Wagtail content intact, so it is safe to edit off-site and write back later:

```sh
# Page 3's body field, as Markdown with references preserved
curl "$BASE/pages/3/?rich_text_format=db_markdown" \
  -H "Authorization: Bearer $TOKEN"
```

The body field is returned in the `db_markdown` format, for example:

```json
{
    "body": "# Hello\n\nRead more on [our about page](wagtail://page?id=7)."
}
```

Make a small edit and send it back on the same field, wrapped in a `db_markdown` envelope. Because `body` is a top-level page rich text field, the string and envelope input formats are guaranteed; the value is converted to database HTML for storage.

```sh
curl -X PATCH "$BASE/pages/3/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "body": {
      "format": "db_markdown",
      "content": "# Hello\n\nRead more on [our about page](wagtail://page?id=7) and [our report](wagtail://document?id=4)."
    }
  }'
```

To serve the same content to a public front-end, read it again with `?rich_text_format=html`. This returns display-ready HTML, with the internal `wagtail://` references resolved to public URLs such as page URLs and image rendition URLs:

```sh
curl "$BASE/pages/3/?rich_text_format=html"
```

Because `html` resolution expands the internal identifiers, it is ideal for rendering but not for a second round-trip: writing the resolved HTML back would not preserve the original `wagtail://` references. Use `db_markdown` whenever you need to move content between systems and back without losing links to other Wagtail content.
