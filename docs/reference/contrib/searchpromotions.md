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
        <li>
            <a href="{% pageurl search_promotion.page %}">
                <h2>{{ search_promotion.page.title }}</h2>
                <p>{{ search_promotion.description }}</p>
            </a>
        </li>
    {% endfor %}
</ul>
```
