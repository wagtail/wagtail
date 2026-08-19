(api_v3_images)=

# Images

The v3 API has wide "read" and "write" support for images. You can list, read, upload, update metadata for, and delete images, with the same collection permissions, validation, and behaviour as the admin.

```{note}
Image reads are public by default; uploads, metadata updates, and deletes always require an authenticated request from an account with the relevant permissions. See [](api_v3_authentication) and the collection behaviour below.
```

## Reading images

The `/images/` endpoint lists images, and the `/images/{id}/` endpoint returns a single image. An image response includes its ID, title, dimensions, the configured descriptive and focal-point fields, its collection, its tags, and its type, detail and download URLs.

Both endpoints are public for anonymous requests, but an image whose collection has a restricted view is excluded when the restriction does not accept the request. An authenticated request can satisfy an applicable restriction through the user's and groups' identities.

### Listing and filtering

The images list supports pagination with `?limit` / `?offset` (see [](api_v3)). You can filter on the image's own fields (`title`, `width`, `height`, plus any `api_fields` the project declares) as exact-match query parameters, order the results, and run full-text search:

```sh
# Images titled "hero", newest first (highest id)
curl "https://example.com/api/v3/images/?title=hero&order=-id"

# Search images for "report"
curl "https://example.com/api/v3/images/?search=report"
```

## Uploading an image

The `/images/` endpoint creates an image and requires an authenticated request and the image `add` permission. It uses `multipart/form-data`: the `file` field contains the image binary, and writable metadata is sent as individual form fields:

```sh
curl -X POST "https://example.com/api/v3/images/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@hero.png" \
  -F "title=Hero" \
  -F "description=A hero image" \
  -F "collection_id=3"
```

The `title` and `file` fields are required. Uploads go through the active image model's admin form, so the same validation applies as in the admin: the collection permission, image corruption checks, allowed extensions, maximum byte size, and maximum pixels.

## Updating image metadata

The `/images/{id}/` endpoint updates an image's writable metadata as JSON. It requires an authenticated request and the image `change` permission:

```sh
curl -X PATCH "https://example.com/api/v3/images/7/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Renamed hero", "focal_point_x": 50, "focal_point_y": 50}'
```

Updating cannot replace the original image binary. Tags are returned in image responses but are not writable through the images API.

## Deleting an image

The `/images/{id}/` endpoint deletes an image. It requires an authenticated request and the image `delete` permission. Deletion is a hard delete.

## Custom image models

The API supports custom models set via `WAGTAILIMAGES_IMAGE_MODEL` (see [](custom_image_model))

## Image renditions

[Renditions](image_renditions) are exposed per-project through `api_fields`, the same mechanism as [in the v2 API](api_v2_images):

```python
from wagtail.images.api.fields import ImageRenditionField


class BlogPage(Page):
    ...

    api_fields = [
        APIField("thumbnail", serializer=ImageRenditionField("fill-300x300")),
    ]
```

There is no dedicated rendition endpoint in the v3 API. Serializer-backed API fields such as `ImageRenditionField` remain readable through the compatibility shim.

## Example: upload an image and use it in a StreamField

This example uploads an image, reads it back to confirm, and then creates a page whose body references the image through an image chooser block. It assumes a `BASE` pointing at the mounted API, a bearer `TOKEN`, and a `BlogPage` whose body StreamField includes an image chooser block.

Upload the file and capture the returned image ID. The response is the JSON image detail from the create endpoint:

```sh
curl -X POST "$BASE/images/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@hero.png" \
  -F "title=Hero"
```

Read the image back to confirm it is stored:

```sh
curl "$BASE/images/42/"
```

Then create a page whose body references the image by ID in an image chooser block, using the StreamField block-list representation described in [](api_v3_streamfield):

```sh
curl -X POST "$BASE/pages/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {"type": "blog.BlogPage", "parent_id": 3},
    "title": "Example",
    "body": [
      {"type": "heading", "id": "0e3b2f5c-0000-0000-0000-000000000001", "value": "Example"},
      {"type": "image", "id": "0e3b2f5c-0000-0000-0000-000000000002", "value": 42}
    ]
  }'
```

## Images reference

We document the full generated OpenAPI reference for every image endpoint from Wagtail's own OpenAPI snapshot, see [](api_v3_reference).
