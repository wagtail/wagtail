# Set up site menu for linking to the homepage and other pages

This section of the tutorial will teach you how to create a site menu to link to your homepage and other pages as you add them. The site menu will appear across all pages of your portfolio website, just like your footer.

Start by creating a template tag in your `base/templatetags/navigation_tags.py` file:

```python
from django import template

# import site:
from wagtail.models import Site

from base.models import FooterText

register = template.Library()


# ... keep the definition of get_footer_text and add the get_site_root template tag:
@register.simple_tag(takes_context=True)
def get_site_root(context):
    return Site.find_for_request(context["request"]).root_page
```

In the preceding code, you created the `get_site_root` template tag to retrieve the root page of your site, which is your `HomePage` in this case.

Now, create `mysite/templates/includes/header.html` file and add the following to it:

```html+django
{% load wagtailcore_tags navigation_tags %}

<header>
    {% get_site_root as site_root %}
    <nav>
        <p>
        <a href="{% pageurl site_root %}">Home</a> |
        {% for menuitem in site_root.get_children.live.in_menu %}
            <a href="{% pageurl menuitem %}">{{ menuitem.title }}</a>
        {% endfor %}
        </p>
    </nav>
</header>
```

In the preceding template you loaded the `wagtailcore_tags` and `navigation_tags`.
With these tags, you can generate navigation menus for your Wagtail project.

`{% get_site_root as site_root %}` retrieves your HomePage and assigns it to the variable `site_root`.

`<a href="{% pageurl site_root %}">Home</a> |` creates a link to your HomePage by using the pageurl template tag with `site_root` as an argument. It generates a link to your HomePage, with the label **Home**, followed by a pipe symbol `|`, to separate the menu items.

`{% for menuitem in site_root.get_children.live.in_menu %}` is a loop that iterates through the child pages of your HomePage that are live and included in the menu.

Finally, add your `header` template to your `base` template by modifying your `mysite/templates/base.html` file:

```html+django
<body class="{% block body_class %}{% endblock %}">
    {% wagtailuserbar %}

    {# Add your header template to your base template: #}
    {% include "includes/header.html" %}

    {% block content %}{% endblock %}

    {% include "includes/footer.html" %}

    {# Global javascript #}

    <script type="text/javascript" src="{% static 'js/mysite.js' %}"></script>

    {% block extra_js %}
    {# Override this in templates to add extra javascript #}
    {% endblock %}
</body>
```

Now, if you restart your server and reload your homepage, you'll see your site menu with a link to your homepage labeled as **Home**.

(add_pages_to_your_site_menu)=

## Add pages to your site menu

You can add any top-level, like your Home page, Blog index page, Portfolio page, and Form page to the site menu by doing the following:

1. Go to your admin interface.
2. Go to any top-level page.
3. Click **Promote**.
4. Check the **Show in menus** checkbox.

In the next section of this tutorial, we'll show you how to style your site and improve its user experience.

<!-- Provide a diagram to illustrate the checking of the Show in Menu checkbox -->
