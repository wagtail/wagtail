.. _editors-picks:

=======================
Promoted search results
=======================

.. module:: wagtail.contrib.wagtailsearchpicks

.. versionchanged:: 1.1

    Before Wagtail 1.1, promoted search results were implemented in the :mod:`wagtail.wagtailsearch` core module and called "editors picks".

The ``searchpicks`` module provides the models and user interface for managing "Promoted search results" and displaying them in a search results page.

"Promoted search results" allow editors to explicitly link relevant content to search terms, so results pages can contain curated content in addition to results from the search engine.


Installation
============

The ``searchpicks`` module is not enabled by default. To install it, add ``wagtail.contrib.wagtailsearchpicks`` to ``INSTALLED_APPS`` in your project's Django settings file.


.. code-block:: python

    INSTALLED_APPS = [
        ...

        'wagtail.contrib.wagtailsearchpicks',
    ]

This app contains migrations so make sure you run the ``migrate`` django-admin command after installing.


Usage
=====

Once installed, a new menu item called "Promoted search results" should appear in the "Settings" menu. This is where you can assign pages to popular search terms.


Displaying on a search results page
-----------------------------------

To retrieve a list of promoted search results for a particular search query, you can use the ``{% get_search_picks %}`` template tag from the ``wagtailsearchpicks_tags`` templatetag library:

.. code-block:: HTML+Django

    {% load wagtailcore_tags wagtailsearchpicks_tags %}

    ...

    {% get_search_picks search_query as search_picks %}

    <ul>
        {% for search_pick in search_picks %}
            <li>
                <a href="{% pageurl search_pick.page %}">
                    <h2>{{ search_pick.page.title }}</h2>
                    <p>{{ search_pick.description }}</p>
                </a>
            </li>
        {% endfor %}
    </ul>
