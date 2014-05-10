Search
======

Wagtail provides a very comprehensive, extensible, and flexible search interface. In addition, it provides ways to promote search results through "Editor's Picks." Wagtail also collects simple statistics on queries made through the search interface.

Default Page Search
-------------------

Wagtail provides a default frontend search interface which indexes the ``title`` field common to all ``Page``-derived models. Lets take a look at all the components of the search interface.

The most basic search functionality just needs a search box which submits a request. Since this will be reused throughout the site, lets put it in ``mysite/includes/search_box.html`` and then use ``{% include ... %}`` to weave it into templates::

  <form action="{% url 'wagtailsearch_search' %}" method="get">
    <input type="text" name="q"{% if query_string %} value="{{ query_string }}"{% endif %}>
    <input type="submit" value="Search">
  </form>

The form is submitted to the url of the ``wagtailsearch_search`` view, with the search terms variable ``q``. The view will use its own (very) basic search results template.

Lets use our own template for the results, though. First, in your project's ``settings.py``, define a path to your template::

  WAGTAILSEARCH_RESULTS_TEMPLATE = 'mysite/search_results.html'

Next, lets look at the template itself::

  {% extends "mysite/base.html" %}
  {% load pageurl %}

  {% block title %}Search{% if search_results %} Results{% endif %}{% endblock %}

  {% block search_box %}
    {% include "mysite/includes/search_box.html" with query_string=query_string only %}
  {% endblock %}

  {% block content %}
    <h2>Search Results{% if request.GET.q %} for {{ request.GET.q }}{% endif %}</h2>
    <ul>
      {% for result in search_results %}
        <li>
          <h4><a href="{% pageurl result.specific %}">{{ result.specific }}</a></h4>
          {% if result.specific.search_description %}
            {{ result.specific.search_description|safe }}
          {% endif %}
        </li>
      {% empty %}
        <li>No results found</li>
      {% endfor %}
    </ul>
  {% endblock %}

The search view returns a context with a few useful variables.

  ``query_string``
    The terms (string) used to make the search.

  ``search_results``
    A collection of Page objects matching the query.

  ``is_ajax``
    Boolean. This returns Django's ``request.is_ajax()``.

  ``query``
    The Query object matching the terms. The query model provides several class methods for viewing the statistics of all queries, but exposes only one property for single queries, ``query.hits``, which tracks the number of time the search string has been used.




Default Page Search with AJAX
-----------------------------



Editor's Picks
--------------




Indexing Custom Fields & Custom Search Views
--------------------------------------------







Strategies for Total Search Coverage
------------------------------------

Want every field searchable? Every custom model and each of their custom fields? Here's how...



Search Backends
---------------

Wagtail can degrade to a database-backed text search, but we strongly recommend `Elasticsearch`_.

.. _Elasticsearch: http://www.elasticsearch.org/


Default DB Backend
``````````````````
The default DB search backend effectively acts as a ``__icontains`` filter on the ``indexed_fields`` of your models.


Elasticsearch Backend
`````````````````````
If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including `Searchly`_, who offer a free account suitable for testing and development. To use Searchly:

-  Sign up for an account at `dashboard.searchly.com/users/sign\_up`_
-  Use your Searchly dashboard to create a new index, e.g. 'wagtaildemo'
-  Note the connection URL from your Searchly dashboard
-  Update ``WAGTAILSEARCH_ES_URLS`` and ``WAGTAILSEARCH_ES_INDEX`` in
   your local settings
-  Run ``./manage.py update_index``

.. _Searchly: http://www.searchly.com/
.. _dashboard.searchly.com/users/sign\_up: https://dashboard.searchly.com/users/sign_up


Rolling Your Own
````````````````

