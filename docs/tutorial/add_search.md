# Add search to your site

Using the Wagtail `start` command to start your project gives you a built-in search app. This built-in search app provides a simple search functionality for your site.

However, you can customize your search template to suit your portfolio site. To customize your search template, go to your `search/templates/search.html` file and modify it as follows:

```html+django
{% extends "base.html" %}
{% load static wagtailcore_tags %}

{% block body_class %}template-searchresults{% endblock %}

{% block title %}Search{% endblock %}

{% block content %}
<h1>Search</h1>

<form action="{% url 'search' %}" method="get">
    <input type="text" name="query"{% if search_query %} value="{{ search_query }}"{% endif %}>
    <input type="submit" value="Search" class="button">
</form>

{% if search_results %}

{# Add this paragraph to display the details of results found: #}
<p>You searched{% if search_query %} for “{{ search_query }}”{% endif %}, {{ search_results.paginator.count }} result{{ search_results.paginator.count|pluralize }} found.</p>

{# Replace the <ul> HTML element with the <ol> html element: #}
<ol>
    {% for result in search_results %}
    <li>
        <h4><a href="{% pageurl result %}">{{ result }}</a></h4>
        {% if result.search_description %}
        {{ result.search_description }}
        {% endif %}
    </li>
    {% endfor %}
</ol>

{# Improve pagination by adding: #}
{% if search_results.paginator.num_pages > 1 %}
    <p>Page {{ search_results.number }} of {{ search_results.paginator.num_pages }}, showing {{ search_results|length }} result{{ search_results|pluralize }} out of {{ search_results.paginator.count }}</p>
{% endif %}

{% if search_results.has_previous %}
<a href="{% url 'search' %}?query={{ search_query|urlencode }}&amp;page={{ search_results.previous_page_number }}">Previous</a>
{% endif %}

{% if search_results.has_next %}
<a href="{% url 'search' %}?query={{ search_query|urlencode }}&amp;page={{ search_results.next_page_number }}">Next</a>
{% endif %}

{% elif search_query %}
No results found
{% endif %}
{% endblock %}
```

Now, let's explain the customizations you made in the preceding template:

1. You used `<p>You searched{% if search_query %} for “{{ search_query }}”{% endif %}, {{ search_results.paginator.count }} result{{ search_results.paginator.count|pluralize }} found.</p>` to display the search query, the number of results found. You also used it to display the plural form of "result" if more than one search result is found.

2. You replaced the `<ul>` HTML element with the `<ol>` HTML element. The `<ol>` HTML element contains a loop iterating through each search result and displaying them as list items. Using `<ol>` gives you numbered search results.

3. You improved the pagination in the template. `{% if search_results.paginator.num_pages > 1 %}` checks if there is more than one page of search results. If there is more than one page of search results, it displays the current page number, the total number of pages, the number of results on the current page, and the total number of results. `{% if search_results.has_previous %} and {% if search_results.has_next %}` checks if there are previous and next pages of search results. If they exist, it displays "Previous" and "Next" links with appropriate URLs for pagination.

Now, you want to display your search across your site. One way to do this is to add it to your header. Go to your `mysite/templates/includes/header.html` file and modify it as follows:

```html+django
{% load wagtailcore_tags navigation_tags wagtailuserbar %}

<header>
    <a href="#main" class="skip-link">Skip to content</a>
    {% get_site_root as site_root %}
    <nav>
        <p>
          <a href="{% pageurl site_root %}">{{ site_root.title }}</a> |
          {% for menuitem in site_root.get_children.live.in_menu %}
            <a href="{% pageurl menuitem %}">{{ menuitem.title }}</a>{% if not forloop.last %} | {% endif %}
          {% endfor %}

          {# Display your search by adding this: #}
          | <a href="/search/">Search</a>
        </p>
    </nav>

    {% wagtailuserbar "top-right" %}
</header>
```

Well done! You now have a fully deployable portfolio site. The next section of this tutorial will walk you through how to deploy your site.
