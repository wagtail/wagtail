# Style and improve user experience

In this tutorial, you'll add a basic site theme to your portfolio site and improve its user experience.

## Add styles

To style your site, navigate to your `mysite/static/css/mysite.css` file and add the following:

```css
*,
::before,
::after {
    box-sizing: border-box;
}

html {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, Roboto, "Helvetica Neue", Arial, sans-serif, Apple Color Emoji, "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
}

body {
    min-height: 100vh;
    max-width: 800px;
    margin: 0 auto;
    padding: 10px;
    display: grid;
    gap: 3vw;
    grid-template-rows: min-content 1fr min-content;
}

a {
    color: currentColor;
}

footer {
    border-top: 2px dotted;
    text-align: center;
}

header {
    border-bottom: 2px dotted;
}

.template-homepage main {
    text-align: center;
}
```

Now, reload your portfolio site to reflect the styles.

```{note}
If your webpage's styles do not update after reloading, then you may need to clear your browser cache.
```

## Improve user experience

There are several ways to improve the user experience of your portfolio site.

Start by modifying your `mysite/templates/base.html` file as follows:

```html+django
{# Remove wagtailuserbar: #}
{% load static wagtailcore_tags %}

<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="utf-8" />
        <title>
            {% block title %}
            {% if page.seo_title %}{{ page.seo_title }}{% else %}{{ page.title }}{% endif %}
            {% endblock %}
            {% block title_suffix %}
            {% wagtail_site as current_site %}
            {% if current_site and current_site.site_name %}- {{ current_site.site_name }}{% endif %}
            {% endblock %}
        </title>
        {% if page.search_description %}
        <meta name="description" content="{{ page.search_description }}" />
        {% endif %}
        <meta name="viewport" content="width=device-width, initial-scale=1" />

        {# Force all links in the live preview panel to be opened in a new tab #}
        {% if request.in_preview_panel %}
        <base target="_blank">
        {% endif %}

        {# Add supported color schemes: #}
        <meta name="color-scheme" content="light dark">

        {# Add a favicon with inline SVG: #}
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🍩</text></svg>"/>

        {# Global stylesheets #}
        <link rel="stylesheet" type="text/css" href="{% static 'css/mysite.css' %}">

        {% block extra_css %}
        {# Override this in templates to add extra stylesheets #}
        {% endblock %}
    </head>

    <body class="{% block body_class %}{% endblock %}">
        {# Remove  wagtailuserbar: #}

        {% include "includes/header.html" %}

        {# Wrap your block content  within a <main> HTML5 tag: #}
        <main>
            {% block content %}{% endblock %}
        </main>

        {% include "includes/footer.html" %}

        {# Global javascript #}

        <script type="text/javascript" src="{% static 'js/mysite.js' %}"></script>

        {% block extra_js %}
        {# Override this in templates to add extra javascript #}
        {% endblock %}
    </body>
</html>
```

In the preceding template, you made the following modifications:

1. You removed `wagtailuserbar` from your base template. You'll add the `wagtailuserbar` to your `header` template later in the tutorial. This change improves the user experience for keyboard and screen reader users.

2. You Added `<meta name="color-scheme" content="light dark">` to inform the browser about the supported color schemes for your site. This makes your site adapt to both dark and light themes.

3. You used the `<link>` tag to add a favicon to your portfolio site using inline SVG.

4. You wrapped the `{% block content %}` and `{% endblock %}` tags with a `<main>` HTML5 tag. The `<main>` tag is a semantic HTML5 tag used to indicate the main content of a webpage.

Also, you should dynamically get your HomePage's title to use in your site menu instead of hardcoding it in your template. You should include the child pages of the Home page in your site menu if they have their 'Show in menus' option checked. Finally, you want to ensure that you add the `wagtailuserbar` that you removed from your `base` template to your `header` template. This will improve users' experience for keyboard and screen reader users.

To make the improvements mentioned in the preceding paragraph, modify your `mysite/templates/includes/header.html` file as follows:

```html+django
{# Load wagtailuserbar: #}
{% load wagtailcore_tags navigation_tags wagtailuserbar %}

<header>
    {% get_site_root as site_root %}
    <nav>
        <p>
          <a href="{% pageurl site_root %}">{{ site_root.title }}</a> |
          {% for menuitem in site_root.get_children.live.in_menu %}

            {# Add the child pages of your HomePage that have their `Show in menu` checked #}
            <a href="{% pageurl menuitem %}">{{ menuitem.title }}</a>{% if not forloop.last %} | {% endif %}

          {% endfor %}
        </p>
    </nav>

    {# Add wagtailuserbar: #}
    {% wagtailuserbar "top-right" %}
</header>
```

Another way you can improve user experience is by adding a skip link for keyboard users. A skip link is a web accessibility feature that enhances the browsing experience for keyboard navigators and screen readers. The skip link will let your users jump directly to the main content.

To add a skip-link, add the following styles to your `mysite/static/css/mysite.css` file:

```css
.skip-link {
    position: absolute;
    top: -30px;
}

.skip-link:focus-visible {
    top: 5px;
}
```

After adding the styles, go to your `mysite/templates/base.html` file and add a unique identifier:

```html+django
{% include "includes/header.html" %}

{# Add a unique identifier: #}
<main id="main">
  {% block content %}{% endblock %}
</main>
```

Finally, go to your `mysite/templates/includes/header.html` file and modify it as follows:

```
{% load wagtailcore_tags navigation_tags wagtailuserbar %}
<header>
  {# Add this: #}
  <a href="#main" class="skip-link">Skip to content</a>

  {% get_site_root as site_root %}
  <nav>
    <p>
      <a href="{% pageurl site_root %}">{{ site_root.title }}</a> |
      {% for menuitem in site_root.get_children.live.in_menu %}
        <a href="{% pageurl menuitem %}">{{ menuitem.title }}</a>{% if not forloop.last %} | {% endif %}
      {% endfor %}
    </p>
  </nav>
  {% wagtailuserbar "top-right" %}
</header>
```

In the preceding template, you added an `<a> (anchor)` element to create a _Skip to content_ link. You set the `href` attribute to `#main`. The internal anchor links to your base template's `main` element.

Well done! Now, you know how to style a Wagtail site. The next section will teach you how to create a contact page for your portfolio site.
