(api_v3_ref_images)=

# Images endpoint reference

The images router provides upload, retrieve, and delete operations for
Wagtail images, plus rendition generation.

## Base URL

```
/api/v3/images/
```

## Operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v3/images/` | List images |
| `GET` | `/api/v3/images/{id}/` | Retrieve image metadata |
| `POST` | `/api/v3/images/` | Upload a new image (`multipart/form-data`) |
| `PATCH` | `/api/v3/images/{id}/` | Update image title / tags |
| `DELETE` | `/api/v3/images/{id}/` | Delete an image |
| `GET` | `/api/v3/images/{id}/renditions/` | Get renditions for an image |

## Upload request body

Upload uses `multipart/form-data`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | binary | ✅ | The image file (JPEG, PNG, GIF, WebP, AVIF) |
| `title` | string | ✅ | Display title |
| `collection` | int | ❌ | Collection id (defaults to root collection) |
| `tags` | string | ❌ | Comma-separated tags |

## Required permissions

| Operation | Required permission |
|-----------|-------------------|
| List / retrieve | `view` on `wagtailimages.image` |
| Upload | `add` on `wagtailimages.image` |
| Update | `change` on `wagtailimages.image` |
| Delete | `delete` on `wagtailimages.image` |

## See also

- {ref}`api_v3_images` — image upload how-to with code examples.
