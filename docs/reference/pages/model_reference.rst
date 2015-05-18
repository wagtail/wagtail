Page model Reference
====================


``Page`` Class Reference
~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: wagtail.wagtailcore.models
.. autoclass:: Page

    The following Django model fields are provided for all pages and are queryable from ``Page.objects``.

    .. attribute:: title (text)

        Human-readable title of the page.

    .. attribute:: slug (text)

            The slug of the page. This is used for constructing the page's URL.

            For example: ``http://domain.com/blog/[my-slug]/``

    .. attribute:: content_type (foreign key)

            A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` object that represents the specific model of this page.

    .. attribute:: live (boolean)

            A boolean that is set to ``True`` if the page is published.

            Note: this field defaults to ``True`` meaning that any pages that are created programmatically will be published by default.

    .. attribute:: has_unpublished_changes (boolean)

            A boolean that is set to ``True`` when the page is either in draft or published with draft changes.

    .. attribute:: owner (foreign key)

            A foreign key to the user that created the page.

    .. attribute:: first_published_at (date/time)

            The date/time when the page was first published.

    .. attribute:: seo_title (text)

            Alternate SEO-crafted title, for use in the page's ``<title>`` HTML tag.

    .. attribute:: search_description (text)

            SEO-crafted description of the content, used for search indexing. This is also suitable for the page's ``<meta name="description">`` HTML tag.

    .. attribute:: show_in_menus (boolean)

            Toggles whether the page should be included in site-wide menus.

            This is used by the :meth:`~wagtail.wagtailcore.query.PageQuerySet.in_menu` QuerySet filter.

    In addition to the model fields provided, ``Page`` has many properties and methods that you may wish to reference, use, or override in creating your own models. Those listed here are relatively straightforward to use, but consult the Wagtail source code for a full view of what's possible.

    .. autoattribute:: specific

    .. autoattribute:: specific_class

    .. autoattribute:: url

    .. autoattribute:: full_url
    
    .. automethod:: get_verbose_name

    .. automethod:: relative_url

    .. automethod:: is_navigable

    .. automethod:: route

    .. automethod:: serve

    .. automethod:: get_context

    .. automethod:: get_template

    .. autoattribute:: preview_modes

    .. automethod:: serve_preview

    .. automethod:: get_ancestors

    .. automethod:: get_descendants

    .. automethod:: get_siblings

    .. automethod:: search

    .. attribute:: search_fields
        
        A list of fields to be indexed by the search engine. See Search docs :ref:`wagtailsearch_indexing_fields`

    .. attribute:: subpage_types

        A whitelist of page models which can be created as children of this page type e.g a ``BlogIndex`` page might allow ``BlogPage``, but not ``JobPage`` e.g

        .. code-block:: python

            class BlogIndex(Page):
                subpage_types = ['mysite.BlogPage', 'mysite.BlogArchivePage']
                
        The creation of child pages can be blocked altogether for a given page by setting it's subpage_types attribute to an empty array e.g
        
        .. code-block:: python

            class BlogPage(Page):
                subpage_types = []
                
    .. attribute:: parent_page_types

        A whitelist of page models which are allowed as parent page types e.g a ``BlogPage`` may only allow itself to be created below the ``BlogIndex`` page e.g

        .. code-block:: python

            class BlogPage(Page):
                parent_page_types = ['mysite.BlogIndexPage']
                
        Pages can block themselves from being created at all by setting parent_page_types to an empty array (this is useful for creating unique pages that should only be created once) e.g
        
        .. code-block:: python

            class HiddenPage(Page):
                parent_page_types = []

    .. attribute:: password_required_template

        Defines which template file should be used to render the login form for Protected pages using this model. This overrides the default, defined using ``PASSWORD_REQUIRED_TEMPLATE`` in your settings. See :ref:`private_pages`


Other models
------------

``Site``
~~~~~~~~

.. autoclass:: Site

    .. automethod:: find_for_request

    .. autoattribute:: root_url

    .. automethod:: get_site_root_paths

``PageRevision``
~~~~~~~~~~~~~~~~

.. autoclass:: PageRevision

    .. automethod:: as_page_object

    .. automethod:: approve_moderation

    .. automethod:: reject_moderation

    .. automethod:: is_latest_revision

    .. automethod:: publish

``GroupPagePermission``
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: GroupPagePermission

``PageViewRestriction``
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PageViewRestriction

``Orderable`` (abstract)
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Orderable
