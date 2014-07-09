
.. _wagtailsearch_editors_picks:


Editors picks
=============

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