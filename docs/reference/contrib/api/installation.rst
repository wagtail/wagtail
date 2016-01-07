Wagtail API Installation
========================


To install, add ``wagtail.contrib.api`` and ``rest_framework`` to ``INSTALLED_APPS`` in your Django settings and configure a URL for it in ``urls.py``:

.. code-block:: python

    # settings.py

    INSTALLED_APPS = [
        ...
        'wagtail.contrib.api',
        'rest_framework',
    ]

    # urls.py

    from wagtail.contrib.api import urls as wagtailapi_urls

    urlpatterns = [
        ...
        url(r'^api/', include(wagtailapi_urls)),
    ]
