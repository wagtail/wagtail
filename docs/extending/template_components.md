(template_components)=

# Template components

Working with objects that know how to render themselves as elements on an HTML template is a common pattern seen throughout the Wagtail admin. For example, the admin homepage is a view provided by the central `wagtail.admin` app, but brings together information panels sourced from various other modules of Wagtail, such as images and documents (potentially along with others provided by third-party packages). These panels are passed to the homepage via the [`construct_homepage_panels`](construct_homepage_panels) hook, and each one is responsible for providing its own HTML rendering. In this way, the module providing the panel has full control over how it appears on the homepage.

Wagtail implements this pattern using a standard object type known as a **component**. A component is a Python object that provides the following methods and properties:

```{eval-rst}
.. method:: render_html(self, parent_context=None)

Given a context dictionary from the calling template (which may be a :py:class:`Context <django.template.Context>` object or a plain ``dict`` of context variables), returns the string representation to be inserted into the template. This will be subject to Django's HTML escaping rules, so a return value consisting of HTML should typically be returned as a :py:mod:`SafeString <django.utils.safestring>` instance.

.. attribute:: media

A (possibly empty) :doc:`form media <django:topics/forms/media>` object defining JavaScript and CSS resources used by the component.
```

```{note}
   Any object implementing this API can be considered a valid component; it does not necessarily have to inherit from the `Component` class described below, and user code that works with components should not assume this (for example, it must not use `isinstance` to check whether a given value is a component).
```

(creating_template_components)=

## Creating components

The preferred way to create a component is to define a subclass of `wagtail.admin.ui.components.Component` and specify a `template_name` attribute on it. The rendered template will then be used as the component's HTML representation:

```python
from wagtail.admin.ui.components import Component

class WelcomePanel(Component):
    template_name = 'my_app/panels/welcome.html'


my_welcome_panel = WelcomePanel()
```

`my_app/templates/my_app/panels/welcome.html`:

```html+django
<h1>Welcome to my app!</h1>
```

For simple cases that don't require a template, the `render_html` method can be overridden instead:

```python
from django.utils.html import format_html
from wagtail.admin.components import Component

class WelcomePanel(Component):
    def render_html(self, parent_context):
        return format_html("<h1>{}</h1>", "Welcome to my app!")
```

## Passing context to the template

The `get_context_data` method can be overridden to pass context variables to the template. As with `render_html`, this receives the context dictionary from the calling template:

```python
from wagtail.admin.ui.components import Component

class WelcomePanel(Component):
    template_name = 'my_app/panels/welcome.html'

    def get_context_data(self, parent_context):
        context = super().get_context_data(parent_context)
        context['username'] = parent_context['request'].user.username
        return context
```

`my_app/templates/my_app/panels/welcome.html`:

```html+django
<h1>Welcome to my app, {{ username }}!</h1>
```

## Adding media definitions

Like Django form widgets, components can specify associated JavaScript and CSS resources using either an inner `Media` class or a dynamic `media` property:

```python
class WelcomePanel(Component):
    template_name = 'my_app/panels/welcome.html'

    class Media:
        css = {
            'all': ('my_app/css/welcome-panel.css',)
        }
```

## Using components on your own templates

The `wagtailadmin_tags` tag library provides a `{% component %}` tag for including components on a template. This takes care of passing context variables from the calling template to the component (which would not be the case for a basic `{{ ... }}` variable tag). For example, given the view:

```python
from django.shortcuts import render

def welcome_page(request):
    panels = [
        WelcomePanel(),
    ]

    render(request, 'my_app/welcome.html', {
        'panels': panels,
    })
```

the `my_app/welcome.html` template could render the panels as follows:

```html+django
{% load wagtailadmin_tags %}
{% for panel in panels %}
    {% component panel %}
{% endfor %}
```

Note that it is your template's responsibility to output any media declarations defined on the components. For a Wagtail admin view, this is best done by constructing a media object for the whole page within the view, passing this to the template, and outputting it via the base template's `extra_js` and `extra_css` blocks:

```python
from django.forms import Media
from django.shortcuts import render

def welcome_page(request):
    panels = [
        WelcomePanel(),
    ]

    media = Media()
    for panel in panels:
        media += panel.media

    render(request, 'my_app/welcome.html', {
        'panels': panels,
        'media': media,
    })
```

`my_app/welcome.html`:

```html+django
{% extends "wagtailadmin/base.html" %}
{% load wagtailadmin_tags %}

{% block extra_js %}
    {{ block.super }}
    {{ media.js }}
{% endblock %}

{% block extra_css %}
    {{ block.super }}
    {{ media.css }}
{% endblock %}

{% block content %}
    {% for panel in panels %}
        {% component panel %}
    {% endfor %}
{% endblock %}
```
