(api_v2_configuration)=

# Wagtail API v2 Configuration Guide

This section of the docs will show you how to set up a public API for your
Wagtail site.

Even though the API is built on Django REST Framework, you do not need to
install this manually as it is already a dependency of Wagtail.

## Basic configuration

### Enable the app

Firstly, you need to enable Wagtail's API app so Django can see it.
Add `wagtail.api.v2` to `INSTALLED_APPS` in your Django project settings:

```python
# settings.py

INSTALLED_APPS = [
    ...

    'wagtail.api.v2',

    ...
]
```

Optionally, you may also want to add `rest_framework` to `INSTALLED_APPS`.
This would make the API browsable when viewed from a web browser but is not
required for basic JSON-formatted output.

### Configure endpoints

Next, it's time to configure which content will be exposed on the API. Each
content type (such as pages, images and documents) has its own endpoint.
Endpoints are combined by a router, which provides the url configuration you
can hook into the rest of your project.

Wagtail provides three endpoint classes you can use:

-   Pages {class}`wagtail.api.v2.views.PagesAPIViewSet`
-   Images {class}`wagtail.images.api.v2.views.ImagesAPIViewSet`
-   Documents {class}`wagtail.documents.api.v2.views.DocumentsAPIViewSet`

You can subclass any of these endpoint classes to customize their functionality.
Additionally, there is a base endpoint class you can use for adding different
content types to the API: `wagtail.api.v2.views.BaseAPIViewSet`

For this example, we will create an API that includes all three builtin content
types in their default configuration:

```python
# api.py

from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet

# Create the router. "wagtailapi" is the URL namespace
api_router = WagtailAPIRouter('wagtailapi')

# Add the three endpoints using the "register_endpoint" method.
# The first parameter is the name of the endpoint (eg. pages, images). This
# is used in the URL of the endpoint
# The second parameter is the endpoint class that handles the requests
api_router.register_endpoint('pages', PagesAPIViewSet)
api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint('documents', DocumentsAPIViewSet)
```

Next, register the URLs so Django can route requests into the API:

```python
# urls.py

from .api import api_router

urlpatterns = [
    ...

    path('api/v2/', api_router.urls),

    ...

    # Ensure that the api_router line appears above the default Wagtail page serving route
    re_path(r'^', include(wagtail_urls)),
]
```

With this configuration, pages will be available at `/api/v2/pages/`, images
at `/api/v2/images/` and documents at `/api/v2/documents/`

(apiv2_page_fields_configuration)=

### Adding custom page fields

It's likely that you would need to export some custom fields over the API. This
can be done by adding a list of fields to be exported into the `api_fields`
attribute for each page model.

For example:

```python
# blog/models.py

from wagtail.api import apifield

class blogpageauthor(orderable):
    page = models.foreignkey('blog.blogpage', on_delete=models.cascade, related_name='authors')
    name = models.charfield(max_length=255)

    api_fields = [
        apifield('name'),
    ]


class blogpage(page):
    published_date = models.datetimefield()
    body = richtextfield()
    feed_image = models.foreignkey('wagtailimages.image', on_delete=models.set_null, null=true, ...)
    private_field = models.charfield(max_length=255)

    # export fields over the api
    api_fields = [
        apifield('published_date'),
        apifield('body'),
        apifield('feed_image'),
        apifield('authors'),  # this will nest the relevant blogpageauthor objects in the api response
    ]
```

This will make `published_date`, `body`, `feed_image` and a list of
`authors` with the `name` field available in the API. But to access these
fields, you must select the `blog.BlogPage` type using the `?type`
[parameter in the API itself](apiv2_custom_page_fields).

### Custom serializers

[Serializers](https://www.django-rest-framework.org/api-guide/fields) are used to convert the database representation of a model into
JSON format. You can override the serializer for any field using the
`serializer` keyword argument:

```python
from rest_framework.fields import DateField

class BlogPage(Page):
    ...

    api_fields = [
        # Change the format of the published_date field to "Thursday 06 April 2017"
        APIField('published_date', serializer=DateField(format='%A %d %B %Y')),
        ...
    ]
```

Django REST framework's serializers can all take a [source](https://www.django-rest-framework.org/api-guide/fields/#source) argument allowing you
to add API fields that have a different field name or no underlying field at all:

```python
from rest_framework.fields import DateField

class BlogPage(Page):
    ...

    api_fields = [
        # Date in ISO8601 format (the default)
        APIField('published_date'),

        # A separate published_date_display field with a different format
        APIField('published_date_display', serializer=DateField(format='%A %d %B %Y', source='published_date')),
        ...
    ]
```

This adds two fields to the API (other fields omitted for brevity):

```json
{
    "published_date": "2017-04-06",
    "published_date_display": "Thursday 06 April 2017"
}
```

### Images in the API

The `ImageRenditionField` serializer
allows you to add renditions of images into your API. It requires an image
filter string specifying the resize operations to perform on the image. It can
also take the `source` keyword argument described above.

For example:

```python
from wagtail.api import APIField
from wagtail.images.api.fields import ImageRenditionField

class BlogPage(Page):
    ...

    api_fields = [
        # Adds information about the source image (eg, title) into the API
        APIField('feed_image'),

        # Adds a URL to a rendered thumbnail of the image to the API
        APIField('feed_image_thumbnail', serializer=ImageRenditionField('fill-100x100', source='feed_image')),
        ...
    ]
```

This would add the following to the JSON:

```json
{
    "feed_image": {
        "id": 45529,
        "meta": {
            "type": "wagtailimages.Image",
            "detail_url": "http://www.example.com/api/v2/images/12/",
            "download_url": "/media/images/a_test_image.jpg",
            "tags": []
        },
        "title": "A test image",
        "width": 2000,
        "height": 1125
    },
    "feed_image_thumbnail": {
        "url": "/media/images/a_test_image.fill-100x100.jpg",
        "full_url": "http://www.example.com/media/images/a_test_image.fill-100x100.jpg",
        "width": 100,
        "height": 100,
        "alt": "image alt text"
    }
}
```

Note: `download_url` is the original uploaded file path, whereas
`feed_image_thumbnail['url']` is the url of the rendered image.
When you are using another storage backend, such as S3, `download_url` will return
a URL to the image if your media files are properly configured.

## Additional settings

### `WAGTAILAPI_BASE_URL`

(required when using frontend cache invalidation)

This is used in two places, when generating absolute URLs to document files and
invalidating the cache.

Generating URLs to documents will fall back the the current request's hostname
if this is not set. Cache invalidation cannot do this, however, so this setting
must be set when using this module alongside the `wagtailfrontendcache` module.

### `WAGTAILAPI_SEARCH_ENABLED`

(default: True)

Setting this to false will disable full text search. This applies to all
endpoints.

### `WAGTAILAPI_LIMIT_MAX`

(default: 20)

This allows you to change the maximum number of results a user can request at a
time. This applies to all endpoints. Set to `None` for no limit.
