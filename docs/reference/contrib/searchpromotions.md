(editors_picks)=

# Promoted search results

```{eval-rst}
.. module:: wagtail.contrib.search_promotions
```

The `searchpromotions` module provides the models and user interface for managing "Promoted search results" and displaying them in a search results page.

"Promoted search results" allow editors to explicitly link relevant content to search terms, so results pages can contain curated content in addition to results from the search engine.

## Installation

The `searchpromotions` module is not enabled by default. To install it, add `wagtail.contrib.search_promotions` to `INSTALLED_APPS` in your project's Django settings file.

```python
INSTALLED_APPS = [
    ...

    'wagtail.contrib.search_promotions',
]
```

This app contains migrations so make sure you run the `migrate` django-admin command after installing.

## Usage

Once installed, a new menu item called "Promoted search results" should appear in the "Settings" menu. This is where you can assign pages to popular search terms.

### Displaying on a search results page

To retrieve a list of promoted search results for a particular search query, you can use the `{% get_search_promotions %}` template tag from the `wagtailsearchpromotions_tags` templatetag library:

```html+django
{% load wagtailcore_tags wagtailsearchpromotions_tags %}

...

{% get_search_promotions search_query as search_promotions %}

<ul>
    {% for search_promotion in search_promotions %}
        {% if search_promotion.page %}
            <li>
                <a href="{% pageurl search_promotion.page %}">
                    <h2>{{ search_promotion.page.title }}</h2>
                    <p>{{ search_promotion.description }}</p>
                </a>
            </li>
        {% else %}
            <li>
                <a href="{{ search_promotion.external_link_url }}">
                    <h2>{{ search_promotion.external_link_text }}</h2>
                    <p>{{ search_promotion.description }}</p>
                </a>
            </li>
        {% endif %}
    {% endfor %}
</ul>
```

### Managing stored search queries

The `searchpromotions` module keeps a log of search queries as well as the number of daily hits through the `Query` and `QueryDailyHits` models.

```{eval-rst}
.. class:: wagtail.contrib.search_promotions.models.Query

    .. method:: get(query_string)
        :classmethod:

        Retrieves a stored search query or creates a new one if it doesn't exist.

    .. method:: add_hit(date=None)

        Records another daily hit for a search query by creating a new record or incrementing the number of hits for an existing record. Defaults to using the current date but an optional `date` parameter can be passed in.
```

#### Example search view

Here's an example Django view for a search page that records a hit for the search query:

```python
from django.template.response import TemplateResponse

from wagtail.models import Page
from wagtail.contrib.search_promotions.models import Query


def search(request):
    search_query = request.GET.get("query", None)

    if search_query:
        search_results = Page.objects.live().search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "search_query": search_query,
            "search_results": search_results,
        },
    )
```

## Management Commands

(searchpromotions_garbage_collect)=

### `searchpromotions_garbage_collect`

```sh
./manage.py searchpromotions_garbage_collect
```

On high traffic websites, the stored queries and daily hits logs may get large and you may want to clean out old records. This command cleans out all search query logs that are more than one week old (or a number of days configurable through the [`WAGTAILSEARCH_HITS_MAX_AGE`](wagtailsearch_hits_max_age) setting).
