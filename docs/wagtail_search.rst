Search
======

Wagtail provides a very comprehensive, extensible, and flexible search interface. In addition, it provides ways to promote search results through "Editor's Picks." Wagtail also collects simple statistics on queries made through the search interface.

Default Page Search
-------------------

Wagtail provides a default frontend search interface which indexes the ``title`` field common to all ``Page``-derived models. Lets take a look at all the components of the search interface.

The most basic search functionality just needs a search box which submits a request. Since this will be reused throughout the site, lets put it in ``mysite/includes/search_box.html`` and then use ``{% include ... %}`` to weave it into templates:

.. code-block:: django

  <form action="{% url 'wagtailsearch_search' %}" method="get">
    <input type="text" name="q"{% if query_string %} value="{{ query_string }}"{% endif %}>
    <input type="submit" value="Search">
  </form>

The form is submitted to the url of the ``wagtailsearch_search`` view, with the search terms variable ``q``. The view will use its own (very) basic search results template.

Lets use our own template for the results, though. First, in your project's ``settings.py``, define a path to your template:

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE = 'mysite/search_results.html'

Next, lets look at the template itself:

.. code-block:: django

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

The search view provides a context with a few useful variables.

  ``query_string``
    The terms (string) used to make the search.

  ``search_results``
    A collection of Page objects matching the query. The ``specific`` property of ``Page`` will give the most-specific subclassed model object for the Wagtail page. For instance, if an ``Event`` model derived from the basic Wagtail ``Page`` were included in the search results, you could use ``specific`` to access the custom properties of the ``Event`` model (``result.specific.date_of_event``).

  ``is_ajax``
    Boolean. This returns Django's ``request.is_ajax()``.

  ``query``
    A Wagtail Query object matching the terms. The query model provides several class methods for viewing the statistics of all queries, but exposes only one property for single objects, ``query.hits``, which tracks the number of time the search string has been used over the lifetime of the site.

Asyncronous Search with JSON and AJAX
-------------------------------------

Wagtail's provides JSON search results when queries are made to the ``wagtailsearch_suggest`` view. To take advantage of it, we need a way to make that URL available to a static script. Instead of hard-coding it, lets set a global variable in our ``base.html``:

.. code-block:: django

  <script>
    var wagtailJSONSearchURL = "{% url 'wagtailsearch_suggest' %}";
  </script>

Lets also add a simple interface for the search with an ``<input>`` element and ``<div>`` for the results:

.. code-block:: html

  <div>
    <h3>Search</h3>
    <input id="json-search" type="text">
    <div id="json-results"></div>
  </div>

Finally, we'll use JQuery to make the aynchronous requests and handle the interactivity:

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

What if you wanted access to the rest of the results context or didn't feel like using JSON? Wagtail also provides a generalized AJAX interface where you can use your own template to serve results asyncronously.

The AJAX interface uses the same view as the normal HTML search, ``wagtailsearch_search``, but will serve different results if Django classifies the request as AJAX (``request.is_ajax()``). Another entry in your project settings will let you override the template used to serve this response:

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE_AJAX = 'mirrorstage/includes/search_listing.html'

You could provide a template in JSON format with extra properties, such as ``query.hits``, or render an HTML snippet that can go directly into your results ``<div>``. If you need more flexibility, such as multiple formats/templates based on differing requests, you can set up a custom search view.

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

