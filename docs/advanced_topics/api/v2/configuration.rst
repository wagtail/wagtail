.. _api_v2_configuration:

==================================
Wagtail API v2 Configuration Guide
==================================

This section of the docs will show you how to set up a public API for your
Wagtail site.

Even though the API is built on Django REST Framework, you do not need to
install this manually as it is already a dependency of Wagtail.

Basic configuration
===================

Enable the app
--------------

Firstly, you need to enable Wagtail's API app so Django can see it.
Add ``wagtail.api.v2`` to ``INSTALLED_APPS`` in your Django project settings:

.. code-block:: python

    # settings.py

    INSTALLED_APPS = [
        ...

        'wagtail.api.v2',

        ...
    ]

Optionally, you may also want to add ``rest_framework`` to ``INSTALLED_APPS``.
This would make the API browsable when viewed from a web browser but is not
required for basic JSON-formatted output.

Configure endpoints
-------------------

Next, it's time to configure which content will be exposed on the API. Each
content type (such as pages, images and documents) has its own endpoint.
Endpoints are combined by a router, which provides the url configuration you
can hook into the rest of your project.

Wagtail provides three endpoint classes you can use:

 - Pages :class:`wagtail.api.v2.endpoints.PagesAPIEndpoint`
 - Images :class:`wagtail.images.api.v2.endpoints.ImagesAPIEndpoint`
 - Documents :class:`wagtail.documents.api.v2.endpoints.DocumentsAPIEndpoint`

You can subclass any of these endpoint classes to customise their functionality.
Additionally, there is a base endpoint class you can use for adding different
content types to the API: :class:`wagtail.api.v2.endpoints.BaseAPIEndpoint`

For this example, we will create an API that includes all three builtin content
types in their default configuration:

.. code-block:: python

    # api.py

    from wagtail.api.v2.endpoints import PagesAPIEndpoint
    from wagtail.api.v2.router import WagtailAPIRouter
    from wagtail.images.api.v2.endpoints import ImagesAPIEndpoint
    from wagtail.documents.api.v2.endpoints import DocumentsAPIEndpoint

    # Create the router. "wagtailapi" is the URL namespace
    api_router = WagtailAPIRouter('wagtailapi')

    # Add the three endpoints using the "register_endpoint" method.
    # The first parameter is the name of the endpoint (eg. pages, images). This
    # is used in the URL of the endpoint
    # The second parameter is the endpoint class that handles the requests
    api_router.register_endpoint('pages', PagesAPIEndpoint)
    api_router.register_endpoint('images', ImagesAPIEndpoint)
    api_router.register_endpoint('documents', DocumentsAPIEndpoint)

Next, register the URLs so Django can route requests into the API:

.. code-block:: python

    # urls.py

    from .api import api_router

    urlpatterns = [
        ...

        url(r'^api/v2/', api_router.urls),

        ...

        # Ensure that the api_router line appears above the default Wagtail page serving route
        url(r'', include(wagtail_urls)),
    ]

With this configuration, pages will be available at ``/api/v2/pages/``, images
at ``/api/v2/images/`` and documents at ``/api/v2/documents/``

.. _apiv2_page_fields_configuration:

Adding custom page fields
-------------------------

It's likely that you would need to export some custom fields over the API. This
can be done by adding a list of fields to be exported into the ``api_fields``
attribute for each page model.

For example:

.. code-block:: python

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

This will make ``published_date``, ``body``, ``feed_image`` and a list of
``authors`` with the ``name`` field available in the API. But to access these
fields, you must select the ``blog.BlogPage`` type using the ``?type``
:ref:`parameter in the API itself <apiv2_custom_page_fields>`.

Custom serialisers
------------------

Serialisers_ are used to convert the database representation of a model into
JSON format. You can override the serialiser for any field using the
``serializer`` keyword argument:

.. code-block:: python

    from rest_framework.fields import DateField

    class BlogPage(Page):
        ...

        api_fields = [
            # Change the format of the published_date field to "Thursday 06 April 2017"
            APIField('published_date', serializer=DateField(format='%A $d %B %Y')),
            ...
        ]

Django REST framework's serializers can all take a source_ argument allowing you
to add API fields that have a different field name or no underlying field at all:

.. code-block:: python

    from rest_framework.fields import DateField

    class BlogPage(Page):
        ...

        api_fields = [
            # Date in ISO8601 format (the default)
            APIField('published_date'),

            # A separate published_date_display field with a different format
            APIField('published_date_display', serializer=DateField(format='%A $d %B %Y', source='published_date')),
            ...
        ]

This adds two fields to the API (other fields omitted for brevity):

.. code-block:: json

    {
        "published_date": "2017-04-06",
        "published_date_display": "Thursday 06 April 2017"
    }

.. _Serialisers: http://www.django-rest-framework.org/api-guide/fields/
.. _source: http://www.django-rest-framework.org/api-guide/fields/#source

Images in the API
-----------------

The :class:`~wagtail.images.api.fields.ImageRenditionField` serialiser
allows you to add renditions of images into your API. It requires an image
filter string specifying the resize operations to perform on the image. It can
also take the ``source`` keyword argument described above.

For example:

.. code-block:: python

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

This would add the following to the JSON:

.. code-block:: json

    {
        "feed_image": {
            "id": 45529,
            "meta": {
                "type": "wagtailimages.Image",
                "detail_url": "http://www.example.com/api/v2/images/12/",
                "tags": []
            },
            "title": "A test image",
            "width": 2000,
            "height": 1125
        },
        "feed_image_thumbnail": {
            "url": "http://www.example.com/media/images/a_test_image.fill-100x100.jpg",
            "width": 100,
            "height": 100
        }
    }

Additional settings
===================

``WAGTAILAPI_BASE_URL``
-----------------------

(required when using frontend cache invalidation)

This is used in two places, when generating absolute URLs to document files and
invalidating the cache.

Generating URLs to documents will fall back the the current request's hostname
if this is not set. Cache invalidation cannot do this, however, so this setting
must be set when using this module alongside the ``wagtailfrontendcache`` module.

``WAGTAILAPI_SEARCH_ENABLED``
-----------------------------

(default: True)

Setting this to false will disable full text search. This applies to all
endpoints.

``WAGTAILAPI_LIMIT_MAX``
------------------------

(default: 20)

This allows you to change the maximum number of results a user can request at a
time. This applies to all endpoints. Set to ``None`` for no limit.
