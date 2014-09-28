=====================
Page Queryset Methods
=====================

All models that inherit from ``Page`` are given some extra Queryset methods accessible from their ``.objects`` attribute.


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

        # This gets a queryset of live children of the homepage with ``show_in_menus`` set
        menu_items = homepage.get_children().live().in_menu()


Reference
=========

.. automodule:: wagtail.wagtailcore.query
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

    .. automethod:: page

        Example:

        .. code-block:: python

            # Append an extra page to a queryset
            new_queryset = old_queryset | Page.objects.page(page_to_add)

    .. automethod:: not_page

        Example:

        .. code-block:: python

            # Remove a page from a queryset
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

    .. automethod:: sibling_of

        Example:

        .. code-block:: python

            # Get list of siblings
            siblings = Page.objects.sibling_of(current_page)

            # Alternative way
            siblings = current_page.get_siblings()

    .. automethod:: public

        See: :ref:`private_pages`

        .. note::

            This doesn't filter out unpublished pages. If you want to only have published public pages, use ``.live().public()``

        Example:

        .. code-block:: python

            # Find all the pages that are viewable by the public
            all_pages = Page.objects.live().public()

    .. automethod:: search

        See: :ref:`wagtailsearch_searching_pages`

        Example:

        .. code-block:: python

            # Search future events
            results = EventPage.objects.live().filter(date__gt=timezone.now()).search("Hello")
