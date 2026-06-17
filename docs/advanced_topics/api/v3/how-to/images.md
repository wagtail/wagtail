(api_v3_images)=

# How to upload and use images

This guide explains how to upload a new image via the v3 API and reference it
in page content.

## Prerequisites

- Wagtail v3 Write API installed and mounted (see {ref}`api_ninja`).
- The authenticated user has the `add` permission on `wagtailimages.image`.

## Uploading an image

Image upload uses a `multipart/form-data` request. Define a file-upload endpoint
using Django Ninja's `File` and `Form` helpers:

```python
# api.py
from ninja import Router, File, Form
from ninja.files import UploadedFile
from wagtail.images.models import Image

router = Router()


@router.post("/images/")
def upload_image(
    request,
    title: str = Form(...),
    file: UploadedFile = File(...),
):
    """Upload an image and return its id and URL."""
    image = Image(title=title, file=file)
    image.save()
    return {
        "id": image.pk,
        "title": image.title,
        "url": image.file.url,
    }
```

### Example request

```sh
curl -X POST http://localhost:8000/api/v3/images/ \
  -H "Authorization: Bearer <token>" \
  -F "title=A bakery photo" \
  -F "file=@/path/to/photo.jpg"
```

Response:

```json
{"id": 17, "title": "A bakery photo", "url": "/media/images/photo.jpg"}
```

## Referencing an uploaded image in a page

After upload, use the returned `id` to embed the image in a StreamField `image`
block when creating or updating a page:

```json
{
  "type": "image",
  "value": {
    "image": 17,
    "caption": "Fresh sourdough from the bakery"
  }
}
```

See {ref}`api_v3_create_page_streamfield` for the full page-creation flow.

## Generating image renditions

To return pre-sized renditions alongside page data, use
[`get_renditions()`](image_renditions_multiple):

```python
from wagtail.images.models import AbstractRendition
from ninja import ModelSchema
from pydantic import Field


class RenditionSchema(ModelSchema):
    url: str = Field(None, alias="file.url")
    alt: str = Field(None, alias="alt")

    class Config:
        model = AbstractRendition
        model_fields = ["width", "height"]


@router.get("/images/{image_id}/renditions")
def get_renditions(request, image_id: int):
    image = Image.objects.get(pk=image_id)
    renditions = image.get_renditions("fill-800x600|format-webp", "fill-400x300")
    return [RenditionSchema.from_orm(r) for r in renditions.values()]
```

## See also

- [](../../images/index) — Wagtail image documentation.
- {ref}`api_v3_create_page_streamfield` — embedding images in StreamField content.
