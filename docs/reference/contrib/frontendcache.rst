.. _frontend_cache_purging:

Frontend cache invalidator
==========================

Many websites use a frontend cache such as Varnish, Squid, Cloudflare or CloudFront to gain extra performance. The downside of using a frontend cache though is that they don't respond well to updating content and will often keep an old version of a page cached after it has been updated.

This document describes how to configure Wagtail to purge old versions of pages from a frontend cache whenever a page gets updated.


Setting it up
-------------

Firstly, add ``"wagtail.contrib.frontend_cache"`` to your INSTALLED_APPS:

.. code-block:: python

    INSTALLED_APPS = [
      ...

      "wagtail.contrib.frontend_cache"
    ]

The ``wagtailfrontendcache`` module provides a set of signal handlers which will automatically purge the cache whenever a page is published or deleted. These signal handlers are automatically registered when the ``wagtail.contrib.frontend_cache`` app is loaded.


Varnish/Squid
^^^^^^^^^^^^^

Add a new item into the ``WAGTAILFRONTENDCACHE`` setting and set the ``BACKEND`` parameter to ``wagtail.contrib.frontend_cache.backends.HTTPBackend``. This backend requires an extra parameter ``LOCATION`` which points to where the cache is running (this must be a direct connection to the server and cannot go through another proxy).

.. code-block:: python

    # settings.py

    WAGTAILFRONTENDCACHE = {
        'varnish': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
            'LOCATION': 'http://localhost:8000',
        },
    }
    WAGTAILFRONTENDCACHE_LANGUAGES = []


Set ``WAGTAILFRONTENDCACHE_LANGUAGES`` to a list of languages (typically equal to ``[l[0] for l in settings.LANGUAGES]``) to also purge the urls for each language of a purging url. This setting needs ``settings.USE_I18N`` to be ``True`` to work. Its default is an empty list.

Finally, make sure you have configured your frontend cache to accept PURGE requests:

- `Varnish <https://www.varnish-cache.org/docs/3.0/tutorial/purging.html>`_
- `Squid <https://wiki.squid-cache.org/SquidFaq/OperatingSquid#How_can_I_purge_an_object_from_my_cache.3F>`_


.. _frontendcache_cloudflare:

Cloudflare
^^^^^^^^^^

Firstly, you need to register an account with Cloudflare if you haven't already got one. You can do this here: `Cloudflare Sign up <https://www.cloudflare.com/sign-up>`_

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.frontend_cache.backends.CloudflareBackend``.

This backend can be configured to use an account-wide API key, or an API token with restricted access.

To use an account-wide API key, find the key `as described in the Cloudflare documentation <https://support.cloudflare.com/hc/en-us/articles/200167836-Managing-API-Tokens-and-Keys#12345682>`_ and specify ``EMAIL`` and ``API_KEY`` parameters.

To use a limited API token, `create a token <https://support.cloudflare.com/hc/en-us/articles/200167836-Managing-API-Tokens-and-Keys#12345680>`_ configured with the 'Zone, Cache Purge' permission and specify the ``BEARER_TOKEN`` parameter.

A ``ZONEID`` parameter will need to be set for either option. To find the ``ZONEID`` for your domain, read the `Cloudflare API Documentation <https://developers.cloudflare.com/fundamentals/get-started/basic-tasks/find-account-and-zone-ids/>`_.

With an API key:

.. code-block:: python

    # settings.py

    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'EMAIL': 'your-cloudflare-email-address@example.com',
            'API_KEY': 'your cloudflare api key',
            'ZONEID': 'your cloudflare domain zone id',
        },
    }

With an API token:

.. code-block:: python

    # settings.py

    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'BEARER_TOKEN': 'your cloudflare bearer token',
            'ZONEID': 'your cloudflare domain zone id',
        },
    }

.. _frontendcache_aws_cloudfront:

Amazon CloudFront
^^^^^^^^^^^^^^^^^

Within Amazon Web Services you will need at least one CloudFront web distribution. If you don't have one, you can get one here: `CloudFront getting started <https://aws.amazon.com/cloudfront/>`_

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.frontend_cache.backends.CloudfrontBackend``. This backend requires one extra parameter, ``DISTRIBUTION_ID`` (your CloudFront generated distribution id).

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'cloudfront': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
            'DISTRIBUTION_ID': 'your-distribution-id',
        },
    }

Configuration of credentials can done in multiple ways. You won't need to store them in your Django settings file. You can read more about this here: `Boto 3 Docs <https://boto3.readthedocs.org/en/latest/guide/configuration.html>`_

In case you run multiple sites with Wagtail and each site has its CloudFront distribution, provide a mapping instead of a single distribution. Make sure the mapping matches with the hostnames provided in your site settings.

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'cloudfront': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudfrontBackend',
            'DISTRIBUTION_ID': {
                'www.wagtail.org': 'your-distribution-id',
                'www.madewithwagtail.org': 'your-distribution-id',
            },
        },
    }

.. note::
    In most cases, absolute URLs with ``www`` prefixed domain names should be used in your mapping. Only drop the ``www`` prefix if you're absolutely sure you're not using it (e.g. a subdomain).

Azure CDN
^^^^^^^^^

With `Azure CDN <https://azure.microsoft.com/en-gb/services/cdn/>`_ you will need a CDN profile with an endpoint configured.

.. _azure-mgmt-cdn: https://pypi.org/project/azure-mgmt-cdn/
.. _azure-identity: https://pypi.org/project/azure-identity/
.. _azure-mgmt-resource: https://pypi.org/project/azure-mgmt-resource/

The third-party dependencies of this backend are:

+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| PyPI Package            | Essential | Reason                                                                                                                                |
+=========================+===========+=======================================================================================================================================+
| azure-mgmt-cdn_         | Yes       | Interacting with the CDN service.                                                                                                     |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| azure-identity_         | No        | Obtaining credentials. It's optional if you want to specify your own credential using a ``CREDENTIALS`` setting (more details below). |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| azure-mgmt-resource_    | No        | For obtaining the subscription ID. Redundant if you want to explicitly specify a ``SUBSCRIPTION_ID`` setting (more details below).    |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.frontend_cache.backends.AzureCdnBackend``. This backend requires the following settings to be set:

* ``RESOURCE_GROUP_NAME`` - the resource group that your CDN profile is in.
* ``CDN_PROFILE_NAME`` - the profile name of the CDN service that you want to use.
* ``CDN_ENDPOINT_NAME`` - the name of the endpoint you want to be purged.

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'azure_cdn': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.AzureCdnBackend',
            'RESOURCE_GROUP_NAME': 'MY-WAGTAIL-RESOURCE-GROUP',
            'CDN_PROFILE_NAME': 'wagtailio',
            'CDN_ENDPOINT_NAME': 'wagtailio-cdn-endpoint-123',
        },
    }

By default the credentials will use ``azure.identity.DefaultAzureCredential``. To modify the credential object used, please use ``CREDENTIALS`` setting. Read about your options on the `Azure documentation <https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-authenticate>`_.


.. code-block:: python

    from azure.common.credentials import ServicePrincipalCredentials

    WAGTAILFRONTENDCACHE = {
        'azure_cdn': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.AzureCdnBackend',
            'RESOURCE_GROUP_NAME': 'MY-WAGTAIL-RESOURCE-GROUP',
            'CDN_PROFILE_NAME': 'wagtailio',
            'CDN_ENDPOINT_NAME': 'wagtailio-cdn-endpoint-123',
            'CREDENTIALS': ServicePrincipalCredentials(
                client_id='your client id',
                secret='your client secret',
            )
        },
    }

Another option that can be set is ``SUBSCRIPTION_ID``. By default the first encountered subscription will be used, but if your credential has access to more subscriptions, you should set this to an explicit value.


Azure Front Door
^^^^^^^^^^^^^^^^

With `Azure Front Door <https://azure.microsoft.com/en-gb/services/frontdoor/>`_ you will need a Front Door instance with caching enabled.

.. _azure-mgmt-frontdoor: https://pypi.org/project/azure-mgmt-frontdoor/
.. _azure-identity: https://pypi.org/project/azure-identity/
.. _azure-mgmt-resource: https://pypi.org/project/azure-mgmt-resource/

The third-party dependencies of this backend are:

+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| PyPI Package            | Essential | Reason                                                                                                                                |
+=========================+===========+=======================================================================================================================================+
| azure-mgmt-frontdoor_   | Yes       | Interacting with the Front Door service.                                                                                              |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| azure-identity_         | No        | Obtaining credentials. It's optional if you want to specify your own credential using a ``CREDENTIALS`` setting (more details below). |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+
| azure-mgmt-resource_    | No        | For obtaining the subscription ID. Redundant if you want to explicitly specify a ``SUBSCRIPTION_ID`` setting (more details below).    |
+-------------------------+-----------+---------------------------------------------------------------------------------------------------------------------------------------+

Add an item into the ``WAGTAILFRONTENDCACHE`` and set the ``BACKEND`` parameter to ``wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend``. This backend requires the following settings to be set:

* ``RESOURCE_GROUP_NAME`` - the resource group that your Front Door instance is part of.
* ``FRONT_DOOR_NAME`` - your configured Front Door instance name.

.. code-block:: python

    WAGTAILFRONTENDCACHE = {
        'azure_front_door': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend',
            'RESOURCE_GROUP_NAME': 'MY-WAGTAIL-RESOURCE-GROUP',
            'FRONT_DOOR_NAME': 'wagtail-io-front-door',
        },
    }

By default the credentials will use ``azure.identity.DefaultAzureCredential``. To modify the credential object used, please use ``CREDENTIALS`` setting. Read about your options on the `Azure documentation <https://docs.microsoft.com/en-us/azure/developer/python/azure-sdk-authenticate>`_.


.. code-block:: python

    from azure.common.credentials import ServicePrincipalCredentials

    WAGTAILFRONTENDCACHE = {
        'azure_front_door': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.AzureFrontDoorBackend',
            'RESOURCE_GROUP_NAME': 'MY-WAGTAIL-RESOURCE-GROUP',
            'FRONT_DOOR_NAME': 'wagtail-io-front-door',
            'CREDENTIALS': ServicePrincipalCredentials(
                client_id='your client id',
                secret='your client secret',
            )
        },
    }

Another option that can be set is ``SUBSCRIPTION_ID``. By default the first encountered subscription will be used, but if your credential has access to more subscriptions, you should set this to an explicit value.

Advanced usage
--------------

Invalidating more than one URL per page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, Wagtail will only purge one URL per page. If your page has more than one URL to be purged, you will need to override the ``get_cached_paths`` method on your page type.

.. code-block:: python

    class BlogIndexPage(Page):
        def get_blog_items(self):
            # This returns a Django paginator of blog items in this section
            return Paginator(self.get_children().live().type(BlogPage), 10)

        def get_cached_paths(self):
            # Yield the main URL
            yield '/'

            # Yield one URL per page in the paginator to make sure all pages are purged
            for page_number in range(1, self.get_blog_items().num_pages + 1):
                yield '/?page=' + str(page_number)

Invalidating index pages
^^^^^^^^^^^^^^^^^^^^^^^^

Pages that list other pages (such as a blog index) may need to be purged as
well so any changes to a blog page are also reflected on the index (for example,
a blog post was added, deleted or its title/thumbnail was changed).

To purge these pages, we need to write a signal handler that listens for
Wagtail's ``page_published`` and ``page_unpublished`` signals for blog pages
(note, ``page_published`` is called both when a page is created and updated).
This signal handler would trigger the invalidation of the index page using the
``PurgeBatch`` class which is used to construct and dispatch invalidation requests.

.. code-block:: python

    # models.py
    from django.dispatch import receiver
    from django.db.models.signals import pre_delete

    from wagtail.signals import page_published
    from wagtail.contrib.frontend_cache.utils import PurgeBatch

    ...

    def blog_page_changed(blog_page):
        # Find all the live BlogIndexPages that contain this blog_page
        batch = PurgeBatch()
        for blog_index in BlogIndexPage.objects.live():
            if blog_page in blog_index.get_blog_items().object_list:
                batch.add_page(blog_index)

        # Purge all the blog indexes we found in a single request
        batch.purge()


    @receiver(page_published, sender=BlogPage)
    def blog_published_handler(instance, **kwargs):
        blog_page_changed(instance)


    @receiver(pre_delete, sender=BlogPage)
    def blog_deleted_handler(instance, **kwargs):
        blog_page_changed(instance)


.. _frontend_cache_invalidating_urls:

Invalidating URLs
^^^^^^^^^^^^^^^^^

The ``PurgeBatch`` class provides a ``.add_url(url)`` and a ``.add_urls(urls)``
for adding individual URLs to the purge batch.

For example, this could be useful for purging a single page on a blog index:

.. code-block:: python

    from wagtail.contrib.frontend_cache.utils import PurgeBatch

    # Purge the first page of the blog index
    batch = PurgeBatch()
    batch.add_url(blog_index.url + '?page=1')
    batch.purge()


The ``PurgeBatch`` class
^^^^^^^^^^^^^^^^^^^^^^^^

All of the methods available on ``PurgeBatch`` are listed below:

.. automodule:: wagtail.contrib.frontend_cache.utils
.. autoclass:: PurgeBatch

    .. automethod:: add_url

    .. automethod:: add_urls

    .. automethod:: add_page

    .. automethod:: add_pages

    .. automethod:: purge
