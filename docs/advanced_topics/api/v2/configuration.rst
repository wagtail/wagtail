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
 - Images :class:`wagtail.wagtailimages.api.v2.endpoints.ImagesAPIEndpoint`
 - Documents :class:`wagtail.wagtaildocs.api.v2.endpoints.DocumentsAPIEndpoint`

You can subclass any of these endpoint classes to customise their functionality.
Additionally, there is a base endpoint class you can use for adding different
content types to the API: :class:`wagtail.api.v2.endpoints.BaseAPIEndpoint`

For this example, we will create an API that includes all three builtin content
types in their default configuration:

.. code-block:: python

    # api.py

    from wagtail.api.v2.endpoints import PagesAPIEndpoint
    from wagtail.api.v2.router import WagtailAPIRouter
    from wagtail.wagtailimages.api.v2.endpoints import ImagesAPIEndpoint
    from wagtail.wagtaildocs.api.v2.endpoints import DocumentsAPIEndpoint

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

    class BlogPageAuthor(Orderable):
        page = models.ForeignKey('blog.BlogPage', related_name='authors')
        name = models.CharField(max_length=255)

        api_fields = ['name']


    class BlogPage(Page):
        published_date = models.DateTimeField()
        body = RichTextField()
        feed_image = models.ForeignKey('wagtailimages.Image', ...)
        private_field = models.CharField(max_length=255)

        # Export fields over the API
        api_fields = [
            'published_date',
            'body',
            'feed_image',
            'authors',  # This will nest the relevant BlogPageAuthor objects in the API response
        ]

This will make ``published_date``, ``body``, ``feed_image`` and a list of
``authors`` with the ``name`` field available in the API. But to access these
fields, you must select the ``blog.BlogPage`` type using the ``?type``
:ref:`parameter in the API itself <apiv2_custom_page_fields>`.

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
time. This applies to all endpoints.
