Wagtail API Installation
========================


To install, add ``wagtail.contrib.wagtailapi`` and ``rest_framework`` to ``INSTALLED_APPS`` in your Django settings and configure a URL for it in ``urls.py``:

.. code-block:: python

    # settings.py

    INSTALLED_APPS = [
        ...
        'wagtail.contrib.wagtailapi',
        'rest_framework',
    ]

    # urls.py

    from wagtail.contrib.wagtailapi import urls as wagtailapi_urls

    urlpatterns = [
        ...

        url(r'^api/', include(wagtailapi_urls)),

        ...

        # Ensure that the wagtailapi_urls line appears above the default Wagtail page serving route
        url(r'', include(wagtail_urls)),
    ]
