(api_ninja)=

# How to set up Django Ninja

While Wagtail provides a [built-in API module](api) based on Django REST Framework, it is possible to use other API frameworks.
Here is information on usage with [Django Ninja](https://django-ninja.dev/), an API framework built on Python type hints and [Pydantic](https://docs.pydantic.dev/latest/), which includes built-in support for OpenAPI schemas.

## Basic configuration

Install `django-ninja`. Optionally you can also add `ninja` to your `INSTALLED_APPS` to avoid loading static files externally when using the OpenAPI documentation viewer.

### Create the API

We will create a new `api.py` module next to the existing `urls.py` file in the project root, instantiate the router.

```python
# api.py
from typing import Literal
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Field, ModelSchema, NinjaAPI
from wagtail.models import Page

api = NinjaAPI()
```

Next, register the URLs so Django can route requests into the API. To test this is working, navigate to `/api/docs`, which displays the OpenAPI documentation (with no available endpoints yet).

```python
# urls.py

from .api import api

urlpatterns = [
    ...

    path("api/", api.urls),

    ...

    # Ensure that the api line appears above the default Wagtail page serving route
    path("", include(wagtail_urls)),
]
```

### Our first endpoint

We will create a simple endpoint that returns a list of all pages in the site. We use the `@api.get` operation decorator to define what route the endpoint is available at, and how to format the response: here, using a custom schema we create.

```python
# api.py


class BasePageSchema(ModelSchema):
    url: str = Field(None, alias="get_url")

    class Config:
        model = Page
        model_fields = [
            "id",
            "title",
            "slug",
        ]


@api.get("/pages/", response=list[BasePageSchema])
def list_pages(request: "HttpRequest"):
    return Page.objects.live().public().exclude(id=1)
```

Our custom `BasePageSchema` combines two techniques: [schema generation from Django models](https://django-ninja.dev/guides/response/django-pydantic/), and calculated fields with [aliases](https://django-ninja.dev/guides/response/#aliases). Here, we use an alias to retrieve the page URL.

We can also add an extra `child_of: int = None` parameter to our endpoint to filter the pages by their parent:

```python
@api.get("/pages/", response=list[BasePageSchema])
def list_pages(request: "HttpRequest", child_of: int = None):
    if child_of:
        return get_object_or_404(Page, id=child_of).get_children().live().public()
    # Exclude the page tree root.
    return Page.objects.live().public().exclude(id=1)
```

Ninja treats every parameter of the `list_pages` function as a query parameter. It uses the provided type hint to parse the value, validate it, and generate the OpenAPI schema.

### Adding custom page fields

Next, let’s add a "detail" API endpoint to return a single page of a specific type. We can use the [path parameters](https://django-ninja.dev/guides/input/path-params/) from Ninja to retrieve our `page_id`.
We also create a new schema for a specific page type: here, `BlogPage`, with `BasePageSchema` as a base.

```python
from blog.models import BlogPage


class BlogPageSchema(BasePageSchema, ModelSchema):
    class Config(BasePageSchema.Config):
        model = BlogPage
        model_fields = [
            "intro",
        ]


@api.get("/pages/{page_id}/", response=BlogPageSchema)
def get_page(request: "HttpRequest", page_id: int):
    return get_object_or_404(Page, id=page_id).specific
```

This works well, with the endpoint now returning generic `Page` fields and the `BlogPage` introduction.
But for sites where all page content is served via an API, it could become tedious to create new endpoints for every page type.

### Combining multiple schemas

To reflect that our response may return multiple page types, we use the type hint union syntax to combine multiple schemas.
This allows us to return different page types from the same endpoint.
Here is an example with an additional schema for our `HomePage` type:

```python
from home.models import HomePage


class HomePageSchema(BasePageSchema, ModelSchema):
    class Config(BasePageSchema.Config):
        model = HomePage

@api.get("/pages/{page_id}/", response=BlogPageSchema | HomePageSchema)
def get_page(request: "HttpRequest", page_id: int):
    return get_object_or_404(Page, id=page_id).specific
```

With this in place, we are still missing a way to determine which of the schemas to use for a given page.
We want to do this by page type, adding an extra `content_type` class attribute annotation to our schemas.

- For `BasePageSchema`, we define `content_type: str`, as any page type can use this base.
- For `HomePageSchema`, we set `content_type: Literal["homepage"]`.
- And for `BlogPageSchema`, we set `content_type: Literal["blogpage"]`.

All we need now is to add a [resolver](https://django-ninja.dev/guides/response/#resolvers) calculated field to the `BasePageSchema`, to return the correct content type for each page. Here is the final version of `BasePageSchema`:

```python
class BasePageSchema(ModelSchema):
    url: str = Field(None, alias="get_url")
    content_type: str

    @staticmethod
    def resolve_content_type(page: Page) -> str:
        return page.specific_class._meta.model_name

    class Config:
        model = Page
        model_fields = [
            "id",
            "title",
            "slug",
        ]
```

With this in place, Pydantic is able to validate the page data returned in `get_page` according to one of the schemas in the `response` union.
It then serializes the data according to the specific schema.

### Nested data

Where the page schema references data in separate models, rather than creating new endpoints, we can add the data directly to the page schema.
Here is an example, adding blog page authors (a snippet with a `ParentalManyToManyField`):

```python
class BlogPageSchema(BasePageSchema, ModelSchema):
    content_type: Literal["blogpage"]
    authors: list[str] = []

    class Config(BasePageSchema.Config):
        model = BlogPage
        model_fields = [
            "intro",
        ]

    @staticmethod
    def resolve_authors(page: BlogPage, context) -> list[str]:
        return [author.name for author in page.authors.all()]
```

This could also be done with the `Field` class if the `BlogPage` class had a method to retrieve author names directly: `authors: list[str] = Field([], alias="get_author_names")`.

### Rich text in the API

Rich text fields in Wagtail use a specific internal format, described in [](../../extending/rich_text_internals). They can be added to the schema as `str`, but it’s often more useful for the API to provide a “display” representation, where references to pages and images are replaced with URLs.
This can also be done with [Ninja resolvers](https://django-ninja.dev/guides/response/#resolvers). Here is an example with the `HomePageSchema`:

```python
from wagtail.rich_text import expand_db_html


class HomePageSchema(BasePageSchema, ModelSchema):
    content_type: Literal["homepage"]
    body: str

    class Config(BasePageSchema.Config):
        model = HomePage

    @staticmethod
    def resolve_body(page: HomePage, context) -> str:
        return expand_db_html(page.body)
```

Here, `body` is defined as a `str`, and the resolver uses the `expand_db_html` function to convert the internal representation to HTML.

### Images in the API

We can use a similar technique for images, combining resolvers and aliases to generate the data.
We use the [`get_renditions()` method](image_renditions_multiple) to retrieve the formatted images, and a custom `RenditionSchema` to define their API representation.

```python
from wagtail.images.models import AbstractRendition


class RenditionSchema(ModelSchema):
    # We need to use the Field / alias API for properties
    url: str = Field(None, alias="file.url")
    alt: str = Field(None, alias="alt")

    class Config:
        model = AbstractRendition
        model_fields = [
            "width",
            "height",
        ]
```

On the `BlogPageSchema`, we define our image field as: `main_image: list[RenditionSchema] = []`. Then add the resolver for it:

```python
    @staticmethod
    def resolve_main_image(page: BlogPage) -> list[AbstractRendition]:
        filters = [
            "fill-800x600|format-webp",
            "fill-800x600",
        ]
        if image := page.main_image():
            return image.get_renditions(*filters).values()
        return []
```

In JSON, our `main_image` is now represented as an array, where each item is an object with `url`, `alt`, `width`, and `height` properties.

## OpenAPI documentation

Django Ninja generates [OpenAPI](https://swagger.io/specification/) documentation automatically, based on the defined operations and schemas.
This also includes a documentation viewer, with support to try out the API directly from the browser. With the above example, you can try accessing the docs at `/api/docs`.

To make the most of this capability, consider the supported [operations parameters](https://django-ninja.dev/reference/operations-parameters/).
