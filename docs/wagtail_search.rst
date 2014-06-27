
.. _search:

Search
======

Wagtail provides a comprehensive and extensible search interface. In addition, it provides ways to promote search results through "Editor's Picks." Wagtail also collects simple statistics on queries made through the search interface.

Default Page Search
-------------------

Wagtail provides a default frontend search interface which indexes the ``title`` field common to all ``Page``-derived models. Let's take a look at all the components of the search interface.

The most basic search functionality just needs a search box which submits a request. Since this will be reused throughout the site, let's put it in ``mysite/includes/search_box.html`` and then use ``{% include ... %}`` to weave it into templates:

.. code-block:: django

  <form action="{% url 'wagtailsearch_search' %}" method="get">
    <input type="text" name="q"{% if query_string %} value="{{ query_string }}"{% endif %}>
    <input type="submit" value="Search">
  </form>

The form is submitted to the url of the ``wagtailsearch_search`` view, with the search terms variable ``q``. The view will use its own basic search results template.

Let's use our own template for the results, though. First, in your project's ``settings.py``, define a path to your template:

.. code-block:: python

  WAGTAILSEARCH_RESULTS_TEMPLATE = 'mysite/search_results.html'

Next, let's look at the template itself:

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
    A Wagtail ``Query`` object matching the terms. The ``Query`` model provides several class methods for viewing the statistics of all queries, but exposes only one property for single objects, ``query.hits``, which tracks the number of time the search string has been used over the lifetime of the site. ``Query`` also joins to the Editor's Picks functionality though ``query.editors_picks``. See :ref:`editors-picks`.

Editor's Picks
--------------

Editor's Picks are a way of explicitly linking relevant content to search terms, so results pages can contain curated content instead of being at the mercy of the search algorithm. In a template using the search results view, editor's picks can be accessed through the variable ``query.editors_picks``. To include editor's picks in your search results template, use the following properties.

``query.editors_picks.all``
  This gathers all of the editor's picks objects relating to the current query, in order according to their sort order in the Wagtail admin. You can then iterate through them using a ``{% for ... %}`` loop. Each editor's pick object provides these properties:

  ``editors_pick.page``
    The page object associated with the pick. Use ``{% pageurl editors_pick.page %}`` to generate a URL or provide other properties of the page object.

  ``editors_pick.description``
    The description entered when choosing the pick, perhaps explaining why the page is relevant to the search terms.

Putting this all together, a block of your search results template displaying editor's Picks might look like this:

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

Finally, we'll use JQuery to make the asynchronous requests and handle the interactivity:

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

.. _editors-picks:


Indexing Custom Fields & Custom Search Views
--------------------------------------------

This functionality is still under active development to provide a streamlined interface, but take a look at ``wagtail/wagtail/wagtailsearch/views/frontend.py`` if you are interested in coding custom search views.


Search Backends
---------------

Wagtail can degrade to a database-backed text search, but we strongly recommend `Elasticsearch`_.

.. _Elasticsearch: http://www.elasticsearch.org/


Default DB Backend
``````````````````
The default DB search backend uses Django's ``__icontains`` filter.


Elasticsearch Backend
`````````````````````
Prerequisites are the Elasticsearch service itself and, via pip, the `elasticsearch-py`_ package:

.. code-block:: guess

  pip install elasticsearch

.. note::
  If you are using Elasticsearch < 1.0, install elasticsearch-py version 0.4.5: ```pip install elasticsearch==0.4.5```

The backend is configured in settings:

.. code-block:: python

  WAGTAILSEARCH_BACKENDS = {
      'default': {
          'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch.ElasticSearch',
          'URLS': ['http://localhost:9200'],
          'INDEX': 'wagtail',
          'TIMEOUT': 5,
          'FORCE_NEW': False,
      }
  }

Other than ``BACKEND`` the keys are optional and default to the values shown. ``FORCE_NEW`` is used by elasticsearch-py. In addition, any other keys are passed directly to the Elasticsearch constructor as case-sensitive keyword arguments (e.g. ``'max_retries': 1``).

If you prefer not to run an Elasticsearch server in development or production, there are many hosted services available, including `Searchly`_, who offer a free account suitable for testing and development. To use Searchly:

-  Sign up for an account at `dashboard.searchly.com/users/sign\_up`_
-  Use your Searchly dashboard to create a new index, e.g. 'wagtaildemo'
-  Note the connection URL from your Searchly dashboard
-  Configure ``URLS`` and ``INDEX`` in the Elasticsearch entry in ``WAGTAILSEARCH_BACKENDS``
-  Run ``./manage.py update_index``

.. _elasticsearch-py: http://elasticsearch-py.readthedocs.org
.. _Searchly: http://www.searchly.com/
.. _dashboard.searchly.com/users/sign\_up: https://dashboard.searchly.com/users/sign_up

Rolling Your Own
````````````````
Wagtail search backends implement the interface defined in ``wagtail/wagtail/wagtailsearch/backends/base.py``. At a minimum, the backend's ``search()`` method must return a collection of objects or ``model.objects.none()``. For a fully-featured search backend, examine the Elasticsearch backend code in ``elasticsearch.py``.
