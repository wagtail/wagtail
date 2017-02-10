Wagtail API Usage Guide
=======================

Listing views
-------------

Performing a ``GET`` request against one of the endpoints will get you a listing of objects in that endpoint. The response will look something like this:

.. code-block:: text

    GET /api/v1/endpoint_name/

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": "total number of results"
        },
        "endpoint_name": [
            {
                "id": 1,
                "meta": {
                    "type": "app_name.ModelName",
                    "detail_url": "http://api.example.com/api/v1/endpoint_name/1/"
                },
                "field": "value"
            },
            {
                "id": 2,
                "meta": {
                    "type": "app_name.ModelName",
                    "detail_url": "http://api.example.com/api/v1/endpoint_name/2/"
                },
                "field": "different value"
            }
        ]
    }


This is the basic structure of all of the listing views. They all have a ``meta`` section with a ``total_count`` variable and a listing of things.


Detail views
------------

All of the endpoints also contain a "detail" view which returns information on an individual object. This view is always accessed by appending the id of the object to the URL.


The ``pages`` endpoint
----------------------

This endpoint includes all live pages in your site that have not been put in a private section.


The listing view (``/api/v1/pages/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is what a typical response from a ``GET`` request to this listing would look like:

.. code-block:: text

    GET /api/v1/pages/

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 2
        },
        "pages": [
            {
                "id": 2,
                "meta": {
                    "type": "demo.HomePage",
                    "detail_url": "http://api.example.com/api/v1/pages/2/"
                },
                "title": "Homepage"
            },
            {
                "id": 3,
                "meta": {
                    "type": "demo.BlogIndexPage",
                    "detail_url": "http://api.example.com/api/v1/pages/3/"
                },
                "title": "Blog"
            }
        ]
    }


Each page object contains the ``id``, a ``meta`` section and the fields with their values.


``meta``
^^^^^^^^

This section is used to hold "metadata" fields which aren't fields in the database. Wagtail API adds two by default:

 - ``type`` - The app label/model name of the object
 - ``detail_url`` - A URL linking to the detail view for this object


Selecting a page type
^^^^^^^^^^^^^^^^^^^^^

Most Wagtail sites are made up of multiple different types of page that each have their own specific fields. In order to view/filter/order on fields specific to one page type, you must select that page type using the ``type`` query parameter.


The ``type`` query parameter must be set to the Pages model name in the format: ``app_label.ModelName``.

.. code-block:: text

    GET /api/v1/pages/?type=demo.BlogPage

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "pages": [
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "My blog 1"
            },
            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2"
            },
            {
                "id": 6,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/6/"
                },
                "title": "My blog 3"
            }
        ]
    }


Specifying a list of fields to return
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As you can see, we still only get the ``title`` field, even though we have selected a type. That's because listing pages require you to explicitly tell it what extra fields you would like to see. You can do this with the ``fields`` query parameter.

Just set ``fields`` to a command-separated list of field names that you would like to use.

.. code-block:: text

    GET /api/v1/pages/?type=demo.BlogPage&fields=title,date_posted,feed_image

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "pages": [
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "My blog 1",
                "date_posted": "2015-01-23",
                "feed_image": {
                    "id": 1,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/1/"
                    }
                }
            },
            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2",
                "date_posted": "2015-01-24",
                "feed_image": {
                    "id": 2,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/2/"
                    }
                }
            },
            {
                "id": 6,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/6/"
                },
                "title": "My blog 3",
                "date_posted": "2015-01-25",
                "feed_image": {
                    "id": 3,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/3/"
                    }
                }
            }
        ]
    }


We now have enough information to make a basic blog listing with a feed image and date that the blog was posted.


Filtering on fields
^^^^^^^^^^^^^^^^^^^

Exact matches on field values can be done by using a query parameter with the same name as the field. Any pages with the field that exactly matches the value of this parameter will be returned.

.. code-block:: text

    GET /api/v1/pages/?type=demo.BlogPage&fields=title,date_posted&date_posted=2015-01-24

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 1
        },
        "pages": [

            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2",
                "date_posted": "2015-01-24",
            }
        ]
    }


Filtering by section of the tree
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is also possible to filter the listing to only include pages with a particular parent or ancestor. This is useful if you have multiple blogs on your site and only want to view the contents of one of them.


**child_of**

Filters the listing to only include direct children of the specified page.

For example, to get all the pages that are direct children of page 7.

.. code-block:: text

    GET /api/v1/pages/?child_of=7

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 1
        },
        "pages": [
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "Other blog 1"
            }
        ]
    }


**descendant_of**

Filters the listing to only include descendants of the specified page.

For example, to get all pages underneath the homepage:

.. code-block:: text

    GET /api/v1/pages/?descendant_of=2

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 1
        },
        "pages": [
            {
                "id": 3,
                "meta": {
                    "type": "demo.BlogIndexPage",
                    "detail_url": "http://api.example.com/api/v1/pages/3/"
                },
                "title": "Blog"
            },
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "My blog 1",
            },
            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2",
            },
            {
                "id": 6,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/6/"
                },
                "title": "My blog 3",
            }
        ]
    }


Ordering
^^^^^^^^

Like filtering, it is also possible to order on database fields. The endpoint accepts a query parameter called ``order`` which should be set to the field name to order by. Field names can be prefixed with a ``-`` to reverse the ordering. It is also possible to order randomly by setting this parameter to ``random``.

.. code-block:: text

    GET /api/v1/pages/?type=demo.BlogPage&fields=title,date_posted,feed_image&order=-date_posted

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "pages": [
            {
                "id": 6,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/6/"
                },
                "title": "My blog 3",
                "date_posted": "2015-01-25",
                "feed_image": {
                    "id": 3,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/3/"
                    }
                }
            },
            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2",
                "date_posted": "2015-01-24",
                "feed_image": {
                    "id": 2,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/2/"
                    }
                }
            },
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "My blog 1",
                "date_posted": "2015-01-23",
                "feed_image": {
                    "id": 1,
                    "meta": {
                        "type": "wagtailimages.Image",
                        "detail_url": "http://api.example.com/api/v1/images/1/"
                    }
                }
            }
        ]
    }


Pagination
^^^^^^^^^^

Pagination is done using two query parameters called ``limit`` and ``offset``. ``limit`` sets the number of results to return and ``offset`` is the index of the first result to return. The default and maximum value for ``limit`` is ``20``. The maximum value can be changed using the ``WAGTAILAPI_LIMIT_MAX`` setting.

.. code-block:: text

    GET /api/v1/pages/?limit=1&offset=1

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 2
        },
        "pages": [
            {
                "id": 3,
                "meta": {
                    "type": "demo.BlogIndexPage",
                    "detail_url": "http://api.example.com/api/v1/pages/3/"
                },
                "title": "Blog"
            }
        ]
    }


Pagination will not change the ``total_count`` value in the meta.


Searching
^^^^^^^^^

To perform a full-text search, set the ``search`` parameter to the query string you would like to search on.

.. code-block:: text

    GET /api/v1/pages/?search=Blog

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "pages": [
            {
                "id": 3,
                "meta": {
                    "type": "demo.BlogIndexPage",
                    "detail_url": "http://api.example.com/api/v1/pages/3/"
                },
                "title": "Blog"
            },
            {
                "id": 4,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/4/"
                },
                "title": "My blog 1",
            },
            {
                "id": 5,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/5/"
                },
                "title": "My blog 2",
            },
            {
                "id": 6,
                "meta": {
                    "type": "demo.BlogPage",
                    "detail_url": "http://api.example.com/api/v1/pages/6/"
                },
                "title": "My blog 3",
            }
        ]
    }


The results are ordered by relevance. It is not possible to use the ``order`` parameter with a search query.

If your Wagtail site is using Elasticsearch, you do not need to select a type to access specific fields. This will search anything that's defined in the models' ``search_fields``.


The detail view (``/api/v1/pages/{id}/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This view gives you access to all of the details for a particular page.

.. code-block:: text

    GET /api/v1/pages/6/

    HTTP 200 OK
    Content-Type: application/json

    {
        "id": 6,
        "meta": {
            "type": "demo.BlogPage",
            "detail_url": "http://api.example.com/api/v1/pages/6/"
        },
        "parent": {
            "id": 3,
            "meta": {
                "type": "demo.BlogIndexPage",
                "detail_url": "http://api.example.com/api/v1/pages/3/"
            }
        },
        "title": "My blog 3",
        "date_posted": "2015-01-25",
        "feed_image": {
            "id": 3,
            "meta": {
                "type": "wagtailimages.Image",
                "detail_url": "http://api.example.com/api/v1/images/3/"
            }
        },
        "related_links": [
            {
                "title": "Other blog page",
                "page": {
                    "id": 5,
                    "meta": {
                        "type": "demo.BlogPage",
                        "detail_url": "http://api.example.com/api/v1/pages/5/"
                    }
                }
            }
        ]
    }


The format is the same as that which is returned inside the listing view, with two additions:
 - All of the available fields are added to the detail page by default
 - A ``parent`` field has been included that contains information about the parent page


The ``images`` endpoint
-----------------------

This endpoint gives access to all uploaded images. This will use the custom image model if one was specified. Otherwise, it falls back to ``wagtailimages.Image``.


The listing view (``/api/v1/images/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is what a typical response from a ``GET`` request to this listing would look like:

.. code-block:: text

    GET /api/v1/images/

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "images": [
            {
                "id": 4,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/4/"
                },
                "title": "Wagtail by Mark Harkin"
            },
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce"
            },
            {
                "id": 6,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/6/"
                },
                "title": "David Mitchell"
            }
        ]
    }


Each image object contains the ``id`` and ``title`` of the image.


Getting ``width``, ``height`` and other fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Like the pages endpoint, the images endpoint supports the ``fields`` query parameter.

By default, this will allow you to add the ``width`` and ``height`` fields to your results. If your Wagtail site uses a custom image model, it is possible to have more.

.. code-block:: text

    GET /api/v1/images/?fields=title,width,height

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "images": [
            {
                "id": 4,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/4/"
                },
                "title": "Wagtail by Mark Harkin",
                "width": 640,
                "height": 427
            },
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce",
                "width": 500,
                "height": 392
            },
            {
                "id": 6,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/6/"
                },
                "title": "David Mitchell",
                "width": 360,
                "height": 282
            }
        ]
    }


Filtering on fields
^^^^^^^^^^^^^^^^^^^

Exact matches on field values can be done by using a query parameter with the same name as the field. Any images with the field that exactly matches the value of this parameter will be returned.

.. code-block:: text

    GET /api/v1/pages/?title=James Joyce

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "images": [
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce"
            }
        ]
    }


Ordering
^^^^^^^^

The images endpoint also accepts the ``order`` parameter which should be set to a field name to order by. Field names can be prefixed with a ``-`` to reverse the ordering. It is also possible to order randomly by setting this parameter to ``random``.

.. code-block:: text

    GET /api/v1/images/?fields=title,width&order=width

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "images": [
            {
                "id": 6,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/6/"
                },
                "title": "David Mitchell",
                "width": 360
            },
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce",
                "width": 500
            },
            {
                "id": 4,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/4/"
                },
                "title": "Wagtail by Mark Harkin",
                "width": 640
            }
        ]
    }


Pagination
^^^^^^^^^^

Pagination is done using two query parameters called ``limit`` and ``offset``. ``limit`` sets the number of results to return and ``offset`` is the index of the first result to return. The default and maximum value for ``limit`` is ``20``. The maximum value can be changed using the ``WAGTAILAPI_LIMIT_MAX`` setting.

.. code-block:: text

    GET /api/v1/images/?limit=1&offset=1

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 3
        },
        "images": [
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce",
                "width": 500,
                "height": 392
            }
        ]
    }


Pagination will not change the ``total_count`` value in the meta.


Searching
^^^^^^^^^

To perform a full-text search, set the ``search`` parameter to the query string you would like to search on.

.. code-block:: text

    GET /api/v1/images/?search=James

    HTTP 200 OK
    Content-Type: application/json

    {
        "meta": {
            "total_count": 1
        },
        "pages": [
            {
                "id": 5,
                "meta": {
                    "type": "wagtailimages.Image",
                    "detail_url": "http://api.example.com/api/v1/images/5/"
                },
                "title": "James Joyce",
                "width": 500,
                "height": 392
            }
        ]
    }


Like the pages endpoint, the results are ordered by relevance and it is not possible to use the ``order`` parameter with a search query.



The detail view (``/api/v1/images/{id}/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This view gives you access to all of the details for a particular image.

.. code-block:: text

    GET /api/v1/images/5/

    HTTP 200 OK
    Content-Type: application/json

    {
        "id": 5,
        "meta": {
            "type": "wagtailimages.Image",
            "detail_url": "http://api.example.com/api/v1/images/5/"
        },
        "title": "James Joyce",
        "width": 500,
        "height": 392
    }


The ``documents`` endpoint
--------------------------

This endpoint gives access to all uploaded documents.


The listing view (``/api/v1/documents/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The documents listing supports the same features as the images listing (documented above) but works with Documents instead.


The detail view (``/api/v1/documents/{id}/``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This view gives you access to all of the details for a particular document.

.. code-block:: text

    GET /api/v1/documents/1/

    HTTP 200 OK
    Content-Type: application/json

    {
        "id": 1,
        "meta": {
            "type": "wagtaildocs.Document",
            "detail_url": "http://api.example.com/api/v1/documents/1/",
            "download_url": "http://api.example.com/documents/1/usage.md"
        },
        "title": "Wagtail API usage"
    }
