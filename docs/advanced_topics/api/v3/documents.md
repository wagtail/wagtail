(api_v3_documents)=

# Documents

Documents are managed through the v3 API at `/api/v3/documents/`. You can list, read, upload, update metadata for, and delete documents, with the same collection permissions, validation, and behaviour as the admin. The document routes are flat rather than nested under collections.

```{note}
Document reads are public by default; uploads, metadata updates, and deletes always require an authenticated bearer token with the relevant document permission. See [](api_v3_authentication) and the collection behaviour below.
```

## Reading documents

The `/documents/` endpoint lists documents, and the `/documents/{id}/` endpoint returns a single document. A document response includes its ID, title, collection, tags, and its type, detail and absolute download URLs.

Both endpoints are public for anonymous requests, but a document is excluded when a view restriction attached **directly to the document's own collection** is not satisfied by the request. A bearer-authenticated request can satisfy an applicable restriction through the user's and groups' identities, and a password-restriction's session state is honoured, in the same way as the documented read behaviour elsewhere in v3.

```{note}
A restriction on an ancestor collection does not hide a document in a descendant collection: only restrictions on the document's own collection affect its visibility.
```

### Listing and filtering

The documents list supports pagination with `?limit` / `?offset` (see [](api_v3)). You can filter on the document's own fields (`id` and `title`, plus any `api_fields` the project declares) as exact-match query parameters, order the results, and run full-text search:

```sh
# Documents titled "report", ordered by title
curl "https://example.com/api/v3/documents/?title=report&order=title"

# Search documents for "policy"
curl "https://example.com/api/v3/documents/?search=policy"
```

## Uploading a document

The `/documents/` endpoint creates a document and requires an authenticated bearer token and the document `add` permission. It uses `multipart/form-data`: the `file` field carries the document binary, and writable metadata is sent as individual form fields:

```sh
curl -X POST "https://example.com/api/v3/documents/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@policy.pdf" \
  -F "title=Acceptable use policy" \
  -F "collection_id=3"
```

The `title` and `file` fields are required. Uploads go through the active document model's admin form, so the same validation applies as in the admin: the collection permission and any configured extension or size restrictions (`WAGTAILDOCS_EXTENSIONS` and `WAGTAILDOCS_MAX_UPLOAD_SIZE`).

```{note}
Extension validation checks the filename and does not verify that the file contents match the extension. See [](user_uploaded_files) for guidance on handling untrusted uploads.
```

## Updating document metadata

The `/documents/{id}/` endpoint updates a document's writable metadata as JSON. It requires an authenticated bearer token and the document `change` permission:

```sh
curl -X PATCH "https://example.com/api/v3/documents/7/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Acceptable use policy (revised)"}'
```

Updating cannot replace the original document binary, and tags are not writable through the documents API.

## Deleting a document

The `/documents/{id}/` endpoint deletes a document. It requires an authenticated bearer token and the document `delete` permission. Deletion is a hard delete, and the document file is cleaned up as part of it.

## Custom document models

The active document model, set with `WAGTAILDOCS_DOCUMENT_MODEL` (see [](custom_document_model)), is used for the API: generated schemas and forms include the model's custom API and admin fields, and its custom form validation. Dedicated tests cover custom model reads, create, update, and schemas.

## Example: upload a document and use it in a page

This example uploads a document, reads it back to confirm, and then creates a page whose rich text links to it using a document reference. It assumes a `BASE` pointing at the mounted API and a bearer `TOKEN`.

Upload the file and capture the returned document ID. The response is the JSON document detail from the create endpoint:

```sh
curl -X POST "$BASE/documents/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@policy.pdf" \
  -F "title=Acceptable use policy"
```

Read the document back to confirm it is stored:

```sh
curl "$BASE/documents/7/"
```

Then create a page whose rich text body links to the document with a `wagtail://document` reference, using the rich text input formats described in [](api_v3_rich_text):

```sh
curl -X POST "$BASE/pages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"type": "blog.BlogPage", "parent_id": 3},
    "title": "Example",
    "body": {
      "format": "db_markdown",
      "content": "Important notices: [our policy](wagtail://document?id=7)."
    }
  }'
```

The full, generated OpenAPI reference for every document endpoint — request and response shapes included — is rendered from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
