Page Attributes, Properties and Methods Reference
-------------------------------------------------

In addition to the model fields provided, ``Page`` has many properties and methods that you may wish to reference, use, or override in creating your own models. Those listed here are relatively straightforward to use, but consult the Wagtail source code for a full view of what's possible.

.. automodule:: wagtail.wagtailcore.models
.. autoclass:: Page

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
