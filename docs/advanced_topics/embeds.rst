.. _embedded_content:

================
Embedded content
================

Wagtail supports generating embed code from URLs to content on external
providers such as Youtube or Twitter. By default, Wagtail will fetch the embed
code directly from the relevant provider's site using the oEmbed protocol.

Wagtail has a built-in list of the most common providers and this list can be
changed :ref:`with a setting <customising_embed_providers>`. Wagtail also supports
fetching embed code using `Embedly`_ and :ref:`custom embed finders <custom_embed_finders>`.

Embedding content on your site
==============================

Wagtail's embeds module should work straight out of the box for most providers.
You can use any of the following methods to call the module:

Rich text
---------

Wagtail's default rich text editor has a "media" icon that allows embeds to be
placed into rich text. You don't have to do anything to enable this; just make
sure the rich text field's content is being passed through the ``|richtext``
filter in the template as this is what calls the embeds module to fetch and
nest the embed code.

``EmbedBlock`` StreamField block type
-------------------------------------

The :class:`~wagtail.wagtailembeds.block.EmbedBlock` block type allows embeds
to be placed into a ``StreamField``.

For example:

.. code-block:: python

    from wagtail.wagtailembeds.blocks import EmbedBlock

    class MyStreamField(blocks.StreamBlock):
        ...

        embed = EmbedBlock()

``{% embed %}`` tag
-------------------

Syntax: ``{% embed <url> [max_width=<max width>] %}``

You can nest embeds into a template by passing the URL and an optional
``max_width`` argument to the ``{% embed %}`` tag.

The ``max_width`` argument is sent to the provider when fetching the embed code.

.. code-block:: html+Django

    {% load wagtailembeds_tags %}

    {# Embed a YouTube video #}
    {% embed 'https://www.youtube.com/watch?v=SJXMTtvCxRo' %}

    {# This tag can also take the URL from a variable #}
    {% embed page.video_url %}

From Python
-----------

You can also call the internal ``get_embed`` function that takes a URL string
and returns an ``Embed`` object (see model documentation below). This also
takes a ``max_width`` keyword argument that is sent to the provider when
fetching the embed code.

.. code-block:: python

    from wagtail.wagtailembeds.embeds import get_embed
    from wagtail.wagtailembeds.exceptions import EmbedException

    try:
        embed = get_embed('https://www.youtube.com/watch?v=SJXMTtvCxRo')

        print(embed.html)
    except EmbedException:
        # Cannot find embed
        pass

.. _configuring_embed_finders:

Configuring embed "finders"
===========================

Embed finders are the modules within Wagtail that are responsible for producing
embed code from a URL.

Embed finders are configured using the ``WAGTAILEMBEDS_FINDERS`` setting. This
is a list of finder configurations that are each run in order until one of them
successfully returns an embed:

The default configuration is:

.. code-block:: python

    WAGTAILEMBEDS_FINDERS = [
        {
            'class': 'wagtail.wagtailembeds.finders.oembed'
        }
    ]

.. _oEmbed:

oEmbed (default)
----------------

The default embed finder fetches the embed code directly from the content
provider using the oEmbed protocol. Wagtail has a built-in list of providers
which are all enabled by default. You can find that provider list at the
following link:

https://github.com/wagtail/wagtail/blob/master/wagtail/wagtailembeds/oembed_providers.py

.. _customising_embed_providers:

Customising the provider list
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can limit which providers may be used by specifying the list of providers
in the finder configuration.

For example, this configuration will only allow content to be nested from Vimeo
and Youtube. It also adds a custom provider:

.. code-block:: python

    from wagtail.wagtailembeds.oembed_providers import youtube, vimeo

    # Add a custom provider
    # Your custom provider must support oEmbed for this to work. You should be
    # able to find these details in the provider's documentation.
    # - 'endpoint' is the URL of the oEmbed endpoint that Wagtail will call
    # - 'urls' specifies which patterns
    my_custom_provider = {
        'endpoint': 'https://customvideosite.com/oembed',
        'urls': [
            '^http(?:s)?://(?:www\\.)?customvideosite\\.com/[^#?/]+/videos/.+$',
        ]
    }

    WAGTAILEMBEDS_FINDERS = [
        {
            'class': 'wagtail.wagtailembeds.finders.oembed',
            'providers': [youtube, vimeo, my_custom_provider],
        }
    ]

Customising an individual provider
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multiple finders can be chained together. This can be used for customising the
configuration for one provider without affecting the others.

For example, this is how you can instruct Youtube to return videos in HTTPS
(which must be done explictly for YouTube):

.. code-block:: python

    from wagtail.wagtailembeds.oembed_providers import youtube


    WAGTAILEMBEDS_FINDERS = [
        # Fetches YouTube videos but puts ``?scheme=https`` in the GET parameters
        # when calling YouTube's oEmbed endpoint
        {
            'class': 'wagtail.wagtailembeds.finders.oembed',
            'providers': [youtube],
            'options': {'scheme': 'https'}
        },

        # Handles all other oEmbed providers the default way
        {
            'class': 'wagtail.wagtailembeds.finders.oembed',
        }
    ]

.. topic:: How Wagtail uses multiple finders

    If multiple providers can handle a URL (for example, a YouTube video was
    requested using the configuration above), the topmost finder is chosen to
    perform the request.

    Wagtail will not try to run any other finder, even if the chosen one didn't
    return an embed.

.. _Embedly:

Embed.ly
--------

`Embed.ly <https://embed.ly>`_ is a paid-for service that can also provide
embeds for sites that do not implement the oEmbed protocol.

They also provide some helpful features such as giving embeds a consistent look
and a common video playback API which is useful if your site allows videos to
be hosted on different providers and you need to implement custom controls for
them.

Wagtail has built in support for fetching embeds from Embed.ly.  To use it, add
an embed finder to your ``WAGTAILEMBEDS_FINDERS`` setting that uses the
``wagtail.wagtailembeds.finders.oembed`` class and pass it your API key:

.. code-block:: python

    WAGTAILEMBEDS_FINDERS = [
        {
            'class': 'wagtail.wagtailembeds.finders.embedly',
            'key': 'YOUR EMBED.LY KEY HERE'
        }
    ]

.. _custom_embed_finders:

Custom embed finder classes
---------------------------

For complete control, you can create a custom finder class.

Here's a stub finder class that could be used as a skeleton; please read the
docstrings for details of what each method does:

.. code-block:: python

    from wagtail.wagtailembeds.finders.base import EmbedFinder


    class ExampleFinder(EmbedFinder):
        def __init__(self, **options):
            pass

        def accept(self, url):
            """
            Returns True if this finder knows how to fetch an embed for the URL.

            This should not have any side effects (no requests to external servers)
            """
            pass

        def find_embed(self, url, max_width=None):
            """
            Takes a URL and max width and returns a dictionary of information about the
            content to be used for embedding it on the site.

            This is the part that may make requests to external APIs.
            """
            # TODO: Perform the request

            return {
                'title': "Title of the content",
                'author_name': "Author name",
                'provider_name': "Provider name (eg. YouTube, Vimeo, etc)",
                'type': "Either 'photo', 'video', 'link' or 'rich'",
                'thumbnail_url': "URL to thumbnail image",
                'width': width_in_pixels,
                'height': height_in_pixels,
                'html': "<h2>The Embed HTML</h2>,
            }

Once you've implemented all of those methods, you just need to add it to your
``WAGTAILEMBEDS_FINDERS`` setting:

.. code-block:: python

    WAGTAILEMBEDS_FINDERS = [
        {
            'class': 'path.to.your.finder.class.here',
            # Any other options will be passed as kwargs to the __init__ method
        }
    ]

The ``Embed`` model
===================

.. class:: wagtail.wagtailembeds.models.Embed

    Embeds are fetched only once and stored in the database so subsequent requests
    for an individual embed do not hit the embed finders again.

    .. attribute:: url

        (text)

        The URL of the original content of this embed.

    .. attribute:: max_width

        (integer, nullable)

        The max width that was requested.

    .. attribute:: type

        (text)

        The type of the embed. This can be either 'video', 'photo', 'link' or 'rich'.

    .. attribute:: html

        (text)

        The HTML content of the embed that should be placed on the page

    .. attribute:: title

        (text)

        The title of the content that is being embedded.

    .. attribute:: author_name

        (text)

        The author name of the content that is being embedded.

    .. attribute:: provider_name

        (text)

        The provider name of the content that is being embedded.

        For example: YouTube, Vimeo

    .. attribute:: thumbnail_url

        (text)

        a URL to a thumbnail image of the content that is being embedded.

    .. attribute:: width

        (integer, nullable)

        The width of the embed (images and videos only).

    .. attribute:: height

        (integer, nullable)

        The height of the embed (images and videos only).

    .. attribute:: last_updated

        (datetime)

        The Date/time when this embed was last fetched.

Deleting embeds
---------------

As long as your embeds configuration is not broken, deleting items in the
``Embed`` model should be perfectly safe to do. Wagtail will automatically
repopulate the records that are being used on the site.

You may want to do this if you've changed from oEmbed to Embedly or vice-versa
as the embed code they generate may be slightly different and lead to
inconsistency on your site.
