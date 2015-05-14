
.. _wagtailsearch_searching:


=========
Searching
=========


.. _wagtailsearch_searching_pages:

Searching Pages
===============

Wagtail provides a ``search`` method on the QuerySet for all page models:

.. code-block:: python

    # Search future EventPages
    >>> from wagtail.wagtailcore.models import EventPage
    >>> EventPage.objects.filter(date__gt=timezone.now()).search("Hello world!")


All methods of ``PageQuerySet`` are supported by ``wagtailsearch``:

.. code-block:: python

    # Search all live EventPages that are under the events index
    >>> EventPage.objects.live().descendant_of(events_index).search("Event")
    [<EventPage: Event 1>, <EventPage: Event 2>]


Searching Images, Documents and custom models
=============================================

You can search these by using the ``search`` method on the search backend:

.. code-block:: python

    >>> from wagtail.wagtailimages.models import Image
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search images
    >>> s = get_search_backend()
    >>> s.search("Hello", Image)
    [<Image: Hello>, <Image: Hello world!>]


You can also pass a QuerySet into the ``search`` method which allows you to add filters to your search results:

.. code-block:: python

    >>> from wagtail.wagtailimages.models import Image
    >>> from wagtail.wagtailsearch.backends import get_search_backend

    # Search images
    >>> s = get_search_backend()
    >>> s.search("Hello", Image.objects.filter(uploaded_by_user=user))
    [<Image: Hello>]


This should work the same way for Documents and custom models as well.


.. _wagtailsearch_frontend_views:


Frontend views
==============


Default Page Search
-------------------

Wagtail provides a default frontend search interface which indexes the ``title`` field common to all ``Page``-derived models. Let's take a look at all the components of the search interface.

The most basic search functionality just needs a search box which submits a request. Since this will be reused throughout the site, let's put it in ``mysite/includes/search_box.html`` and then use ``{% include ... %}`` to weave it into templates:

.. code-block:: django

  <form action="{% url 'wagtailsearch_search' %}" method="get">
    <input type="text" name="q"{% if query_string %} value="{{ query_string }}"{% endif %}>
    <input type="submit" value="Search">
  </form>

The form is submitted to the URL of the ``wagtailsearch_search`` view, with the search terms variable ``q``. The view will use its own basic search results template.

Let's use our own template for the results, though. First, in your project's ``settings.py``, define a path to your template:

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE = 'mysite/search_results.html'

Next, let's look at the template itself:

.. code-block:: django

  {% extends "mysite/base.html" %}
  {% load wagtailcore_tags %}

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

The search view provides a context with a few useful variables.

  ``query_string``
    The terms (string) used to make the search.

  ``search_results``
    A collection of Page objects matching the query. The ``specific`` property of ``Page`` will give the most-specific subclassed model object for the Wagtail page. For instance, if an ``Event`` model derived from the basic Wagtail ``Page`` were included in the search results, you could use ``specific`` to access the custom properties of the ``Event`` model (``result.specific.date_of_event``).

  ``is_ajax``
    Boolean. This returns Django's ``request.is_ajax()``.

  ``query``
    A Wagtail ``Query`` object matching the terms. The ``Query`` model provides several class methods for viewing the statistics of all queries, but exposes only one property for single objects, ``query.hits``, which tracks the number of time the search string has been used over the lifetime of the site. ``Query`` also joins to the Editor's Picks functionality though ``query.editors_picks``. See :ref:`editors-picks`.


Asynchronous Search with JSON and AJAX
--------------------------------------

Wagtail provides JSON search results when queries are made to the ``wagtailsearch_suggest`` view. To take advantage of it, we need a way to make that URL available to a static script. Instead of hard-coding it, let's set a global variable in our ``base.html``:

.. code-block:: django

  <script>
    var wagtailJSONSearchURL = "{% url 'wagtailsearch_suggest' %}";
  </script>

Now add a simple interface for the search with a ``<input>`` element to gather search terms and a ``<div>`` to display the results:

.. code-block:: html

  <div>
    <h3>Search</h3>
    <input id="json-search" type="text">
    <div id="json-results"></div>
  </div>

Finally, we'll use jQuery to make the asynchronous requests and handle the interactivity:

.. code-block:: guess

  $(function() {

    // cache the elements
    var searchBox = $('#json-search'),
      resultsBox = $('#json-results');
    // when there's something in the input box, make the query
    searchBox.on('input', function() {
      if( searchBox.val() == ''){
    resultsBox.html('');
    return;
      }
      // make the request to the Wagtail JSON search view
      $.ajax({
    url: wagtailJSONSearchURL + "?q=" +  searchBox.val(),
    dataType: "json"
      })
      .done(function(data) {
    console.log(data);
    if( data == undefined ){
      resultsBox.html('');
      return;
    }
    // we're in business!  let's format the results
    var htmlOutput = '';
    data.forEach(function(element, index, array){
      htmlOutput += '<p><a href="' + element.url + '">' + element.title + '</a></p>';
    });
    // and display them
    resultsBox.html(htmlOutput);
      })
      .error(function(data){
    console.log(data);
      });
    });

  });

Results are returned as a JSON object with this structure:

.. code-block:: guess

  {
    [
      {
    title: "Lumpy Space Princess",
    url: "/oh-my-glob/"
      },
      {
    title: "Lumpy Space",
    url: "/no-smooth-posers/"
      },
      ...
    ]
  }

What if you wanted access to the rest of the results context or didn't feel like using JSON? Wagtail also provides a generalized AJAX interface where you can use your own template to serve results asynchronously.

The AJAX interface uses the same view as the normal HTML search, ``wagtailsearch_search``, but will serve different results if Django classifies the request as AJAX (``request.is_ajax()``). Another entry in your project settings will let you override the template used to serve this response:

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX = 'myapp/includes/search_listing.html'

In this template, you'll have access to the same context variables provided to the HTML template. You could provide a template in JSON format with extra properties, such as ``query.hits`` and editor's picks, or render an HTML snippet that can go directly into your results ``<div>``. If you need more flexibility, such as multiple formats/templates based on differing requests, you can set up a custom search view.


Custom Search Views
-------------------

This functionality is still under active development to provide a streamlined interface, but take a look at ``wagtail/wagtail/wagtailsearch/views/frontend.py`` if you are interested in coding custom search views.



.. _editors-picks:


Editor's picks
==============

Editor's picks are a way of explicitly linking relevant content to search terms, so results pages can contain curated content in addition to results from the search algorithm. In a template using the search results view, editor's picks can be accessed through the variable ``query.editors_picks``. To include editor's picks in your search results template, use the following properties.

``query.editors_picks.all``
  This gathers all of the editor's picks objects relating to the current query, in order according to their sort order in the Wagtail admin. You can then iterate through them using a ``{% for ... %}`` loop. Each editor's pick object provides these properties:

  ``editors_pick.page``
    The page object associated with the pick. Use ``{% pageurl editors_pick.page %}`` to generate a URL or provide other properties of the page object.

  ``editors_pick.description``
    The description entered when choosing the pick, perhaps explaining why the page is relevant to the search terms.

Putting this all together, a block of your search results template displaying editor's picks might look like this:

.. code-block:: django

  {% with query.editors_picks.all as editors_picks %}
    {% if editors_picks %}
      <div class="well">
      <h3>Editors picks</h3>
    <ul>
      {% for editors_pick in editors_picks %}
        <li>
          <h4>
        <a href="{% pageurl editors_pick.page %}">
          {{ editors_pick.page.title }}
        </a>
          </h4>
          <p>{{ editors_pick.description|safe }}</p>
        </li>
      {% endfor %}
    </ul>
      </div>
    {% endif %}
  {% endwith %}
