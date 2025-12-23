(api_v2_configuration)=

# Wagtail API v2 configuration guide

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

(api_v2_configure_endpoints)=

### Configure endpoints

Next, it's time to configure which content will be exposed on the API. Each
content type (such as pages, images and documents) has its own endpoint.
Endpoints are combined by a router, which provides the url configuration you
can hook into the rest of your project.

Wagtail provides multiple endpoint classes you can use:

-   Pages `wagtail.api.v2.views.PagesAPIViewSet`
-   Images `wagtail.images.api.v2.views.ImagesAPIViewSet`
-   Documents `wagtail.documents.api.v2.views.DocumentsAPIViewSet`
-   Redirects `wagtail.contrib.redirects.api.RedirectsAPIViewSet` see [](redirects_api_endpoint)

You can subclass any of these endpoint classes to customize their functionality.
For example, in this case, if you need to change the `APIViewSet` by setting a desired renderer class:

```python
from rest_framework.renderers import JSONRenderer

# ...

class CustomPagesAPIViewSet(PagesAPIViewSet):
    renderer_classes = [JSONRenderer]
    name = "pages"

api_router.register_endpoint("pages", CustomPagesAPIViewSet)
```

Or changing the desired model to use for page results.

```python
from rest_framework.renderers import JSONRenderer

# ...

class PostPagesAPIViewSet(PagesAPIViewSet):
    model = models.BlogPage


api_router.register_endpoint("posts", PostPagesAPIViewSet)
```

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
# The first parameter is the name of the endpoint (such as pages, images). This
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

from wagtail.api import APIField

class BlogPageAuthor(Orderable):
    page = models.ForeignKey('blog.BlogPage', on_delete=models.CASCADE, related_name='authors')
    name = models.CharField(max_length=255)

    api_fields = [
        APIField('name'),
    ]


class BlogPage(Page):
    published_date = models.DateTimeField()
    body = RichTextField()
    feed_image = models.ForeignKey('wagtailimages.Image', on_delete=models.SET_NULL, null=True, ...)
    private_field = models.CharField(max_length=255)

    # Export fields over the API
    api_fields = [
        APIField('published_date'),
        APIField('body'),
        APIField('feed_image'),
        APIField('authors'),  # This will nest the relevant BlogPageAuthor objects in the API response
    ]
```

This will make `published_date`, `body`, `feed_image` and a list of
`authors` with the `name` field available in the API. But to access these
fields, you must select the `blog.BlogPage` type using the `?type`
[parameter in the API itself](apiv2_custom_page_fields).

(form_page_fields_api_field)=

### Adding form fields to the API

If you have a FormBuilder page called `FormPage` this is an example of how you would expose the form fields to the API:

```python
from wagtail.api import APIField

class FormPage(AbstractEmailForm):
    #...
    api_fields = [
        APIField('form_fields'),
    ]
```

### Custom serializers

[Serializers](https://www.django-rest-framework.org/api-guide/fields/) are used to convert the database representation of a model into
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

### Rich text in the API

In the above example, we serialize the `body` field using Wagtail’s storage format for rich text, described in [](../../../extending/rich_text_internals). This is useful when the API client will directly manipulate the identifiers referencing external data within rich text, such as fetching more data about page links or images by ID.

It’s also often useful for the API to directly provide a “display” representation, similarly to the `|richtext` template filter. This can be done with a custom serializer:

```python
from rest_framework.fields import CharField
from wagtail.rich_text import expand_db_html


class RichTextSerializer(CharField):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return expand_db_html(representation)
```

We can then change our `api_fields` definition so `body` uses this new serializer:

```python
APIField('body', serializer=RichTextSerializer()),
```

(api_v2_images)=

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

For cases where the source image set may contain SVGs, the `ImageRenditionField` constructor takes a `preserve_svg` argument. The behavior of `ImageRenditionField` when `preserve_svg` is `True` is as described for the `image` template tag's `preserve-svg` argument (see the documentation on [](svg_images)).

### Authentication

To protect the access to your API, you can implement an [authentication](https://www.django-rest-framework.org/api-guide/authentication/) method provided by the Django REST Framework, for example the [Token Authentication](https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication):

```python
# api.py

from rest_framework.permissions import IsAuthenticated

# ...

class CustomPagesAPIViewSet(PagesAPIViewSet):
    name = "pages"
    permission_classes = (IsAuthenticated,)


api_router.register_endpoint("pages", CustomPagesAPIViewSet)
```

Extend settings with

```python
# settings.py

INSTALLED_APPS = [
    ...

    'rest_framework.authtoken',

    ...
]

...

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication"
    ],
}
```

Don't forget to run the app's migrations.

Your API endpoint will be accessible only with the Authorization header containing the generated `Token exampleSecretToken123xyz`.
Tokens can be generated in the Django admin under Auth Token or using the `manage.py` command `drf_create_token`.

Note: If you use `TokenAuthentication` in production you must ensure that your API is only available over `https`.

## Additional settings

### `WAGTAILAPI_BASE_URL`

(required when using frontend cache invalidation)

This is used in two places, when generating absolute URLs to document files and
invalidating the cache.

Generating URLs to documents will fall back the current request's hostname
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
Combine with [`?limit` and `?offset` query parameters](apiv2_pagination) to retrieve the desired number of results.
