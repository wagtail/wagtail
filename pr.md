# Pull Request: Safely handle missing attributes in Draftail RichText conversion (#13815)

## PR Title
`Safely handle missing attributes in Draftail RichText conversion (#13815)`

## PR Description

### Overview
This PR fixes a `KeyError` crash that occurred when pasting rich text content (containing images or missing attributes) into the Draftail-based RichText editor. The issue was caused by the conversion logic directly accessing attributes from the HTML/database format without verifying their existence.

The fix adds defensive attribute checks (using `.get()`) to:
- `ImageElementHandler` (for `id` and `format`)
- `MediaEmbedElementHandler` (for `url`)
- `PageLinkElementHandler` (for `id`)

### Checklist
- [x] Use `.get()` for safe attribute access in `ImageElementHandler`.
- [x] Handle missing `url` in `MediaEmbedElementHandler`.
- [x] Gracefully handle missing `id` in `PageLinkElementHandler`.
- [x] Catch `KeyError` during object retrieval where attributes might be missing or malformed.

### Proof
Pasting HTML like `<embed embedtype="image" alt="an image" format="left" />` (missing `id`) or `<embed embedtype="media" />` (missing `url`) no longer causes a server error when reopening the page in the Wagtail admin. The handlers now default to empty values or handle the missing data gracefully, keeping the editor functional.
