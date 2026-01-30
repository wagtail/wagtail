Safely handle missing attributes in Draftail RichText conversion (#13815)

This PR fixes a KeyError crash that could occur when pasting rich text into the Draftail editor if certain embed attributes were missing.

The RichText conversion logic now safely accesses attributes like `id`, `format`, and `url` using `.get()` instead of assuming they are always present. This prevents server errors when handling incomplete or malformed image, embed, or page link data.

Unit tests are added to cover these missing-attribute cases and ensure the editor remains stable.
