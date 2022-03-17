=======================
Page QuerySet reference
=======================

All models that inherit from :class:`~wagtail.models.Page` are given some extra QuerySet methods accessible from their ``.objects`` attribute.


Examples
========

- Selecting only live pages

  .. code-block:: python

      live_pages = Page.objects.live()

- Selecting published EventPages that are descendants of events_index

  .. code-block:: python

      events = EventPage.objects.live().descendant_of(events_index)

- Getting a list of menu items

  .. code-block:: python

      # This gets a QuerySet of live children of the homepage with ``show_in_menus`` set
      menu_items = homepage.get_children().live().in_menu()


Reference
=========

.. automodule:: wagtail.query
.. autoclass:: PageQuerySet

    .. automethod:: live

        Example:

        .. code-block:: python

            published_pages = Page.objects.live()

    .. automethod:: not_live

        Example:

        .. code-block:: python

            unpublished_pages = Page.objects.not_live()

    .. automethod:: in_menu

        Example:

        .. code-block:: python

            # Build a menu from live pages that are children of the homepage
            menu_items = homepage.get_children().live().in_menu()


        .. note::

            To put your page in menus, set the show_in_menus flag to true:

            .. code-block:: python

                # Add 'my_page' to the menu
                my_page.show_in_menus = True

    .. automethod:: not_in_menu

    .. automethod:: in_site

        Example:

        .. code-block:: python

            # Get all the EventPages in the current site
            site = Site.find_for_request(request)
            site_events = EventPage.objects.in_site(site)

    .. automethod:: page

        Example:

        .. code-block:: python

            # Append an extra page to a QuerySet
            new_queryset = old_queryset | Page.objects.page(page_to_add)

    .. automethod:: not_page

        Example:

        .. code-block:: python

            # Remove a page from a QuerySet
            new_queryset = old_queryset & Page.objects.not_page(page_to_remove)

    .. automethod:: descendant_of

        Example:

        .. code-block:: python

            # Get EventPages that are under the special_events Page
            special_events = EventPage.objects.descendant_of(special_events_index)

            # Alternative way
            special_events = special_events_index.get_descendants()

    .. automethod:: not_descendant_of

        Example:

        .. code-block:: python

            # Get EventPages that are not under the archived_events Page
            non_archived_events = EventPage.objects.not_descendant_of(archived_events_index)

    .. automethod:: child_of

        Example:

        .. code-block:: python

            # Get a list of sections
            sections = Page.objects.child_of(homepage)

            # Alternative way
            sections = homepage.get_children()

    .. automethod:: not_child_of

    .. automethod:: ancestor_of

        Example:

        .. code-block:: python

            # Get the current section
            current_section = Page.objects.ancestor_of(current_page).child_of(homepage).first()

            # Alternative way
            current_section = current_page.get_ancestors().child_of(homepage).first()

    .. automethod:: not_ancestor_of

        Example:

        .. code-block:: python

            # Get the other sections
            other_sections = Page.objects.not_ancestor_of(current_page).child_of(homepage)

    .. automethod:: parent_of

    .. automethod:: not_parent_of

    .. automethod:: sibling_of

        Example:

        .. code-block:: python

            # Get list of siblings
            siblings = Page.objects.sibling_of(current_page)

            # Alternative way
            siblings = current_page.get_siblings()

    .. automethod:: not_sibling_of

    .. automethod:: public

        See: :ref:`private_pages`

        .. note::

            This doesn't filter out unpublished pages. If you want to only have published public pages, use ``.live().public()``

        Example:

        .. code-block:: python

            # Find all the pages that are viewable by the public
            all_pages = Page.objects.live().public()

    .. automethod:: not_public

    .. automethod:: search

        See: :ref:`wagtailsearch_searching_pages`

        Example:

        .. code-block:: python

            # Search future events
            results = EventPage.objects.live().filter(date__gt=timezone.now()).search("Hello")

    .. automethod:: type

        Example:

        .. code-block:: python

            # Find all pages that are of type AbstractEmailForm, or one of it's subclasses
            form_pages = Page.objects.type(AbstractEmailForm)

            # Find all pages that are of type AbstractEmailForm or AbstractEventPage, or one of their subclasses
            form_and_event_pages = Page.objects.type(AbstractEmailForm, AbstractEventPage)

    .. automethod:: not_type

    .. automethod:: exact_type

        Example:

        .. code-block:: python

            # Find all pages that are of the exact type EventPage
            event_pages = Page.objects.exact_type(EventPage)

            # Find all page of the exact type EventPage or NewsPage
            news_and_events_pages = Page.objects.exact_type(EventPage, NewsPage)

        .. note::

            If you are only interested in pages of a single type, it is clearer (and often more efficient) to use
            the specific model's manager to get a queryset. For example:

            .. code-block:: python

                event_pages = EventPage.objects.all()

    .. automethod:: not_exact_type

        Example:

        .. code-block:: python

            # First, find all news and event pages
            news_and_events = Page.objects.type(NewsPage, EventPage)

            # Now exclude pages with an exact type of EventPage or NewsPage,
            # leaving only instance of more 'specialist' types
            specialised_news_and_events = news_and_events.not_exact_type(NewsPage, EventPage)

    .. automethod:: unpublish

        Example:

        .. code-block:: python

            # Unpublish current_page and all of its children
            Page.objects.descendant_of(current_page, inclusive=True).unpublish()

    .. automethod:: specific

        Example:

        .. code-block:: python

            # Get the specific instance of all children of the hompage,
            # in a minimum number of database queries.
            homepage.get_children().specific()

        See also: :py:attr:`Page.specific <wagtail.models.Page.specific>`

    .. automethod:: defer_streamfields

        Example:

        .. code-block:: python

            # Apply to a queryset to avoid fetching StreamField values
            # for a specific model
            EventPage.objects.all().defer_streamfields()

            # Or combine with specific() to avoid fetching StreamField
            # values for all models
            homepage.get_children().defer_streamfields().specific()

    .. automethod:: first_common_ancestor
