===========
Wagtail API
===========

The API module provides a public-facing, JSON-formatted API to allow retrieving
content as raw field data. This is useful for cases like serving content to
non-web clients (such as a mobile phone app) or pulling content out of Wagtail
for use in another site.

There are currently two versions of the API available: v1 and v2. Both versions
are "stable" so it is recommended to use v2. V1 is only provided for backwards
compatibility and will be removed from Wagtail soon.

See `RFC 8: Wagtail API <https://github.com/wagtail/rfcs/blob/master/accepted/008-wagtail-api.md#12---stable-and-unstable-versions>`_
for full details on our stabilisation policy.

Version 2 (recommended)
=======================

.. toctree::
    :maxdepth: 2

    v2/configuration
    v2/usage

Version 1
=========

See :doc:`/reference/contrib/api/index`