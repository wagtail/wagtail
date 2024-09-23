(wagtailsnippets_rendering)=

# Rendering snippets

As Django models, snippets can be rendered in Django templates using a custom template tag. Alternatively, they can also be included as part of a Wagtail page's rendering process.

## Including snippets in template tags

The simplest way to make your snippets available to templates is with a template tag. This is mostly done with vanilla Django, so perhaps reviewing Django's documentation for [custom template tags](inv:django#howto/custom-template-tags) will be more helpful. We'll go over the basics, though, and point out any considerations to make for Wagtail.

First, add a new Python file to a `templatetags` folder within your app - for example, `myproject/demo/templatetags/demo_tags.py`. We'll need to load some Django modules and our app's models, and ready the `register` decorator:

```python
from django import template
from demo.models import Advert

register = template.Library()

# ...

# Advert snippets
@register.inclusion_tag('demo/tags/adverts.html', takes_context=True)
def adverts(context):
    return {
        'adverts': Advert.objects.all(),
        'request': context['request'],
    }
```

`@register.inclusion_tag()` takes two variables: a template and a boolean on whether that template should be passed a request context. It's a good idea to include request contexts in your custom template tags, since some Wagtail-specific template tags like `pageurl` need the context to work properly. The template tag function could take arguments and filter the adverts to return a specific instance of the model, but for brevity, we'll just use `Advert.objects.all()`.

Here's what's in the template used by this template tag:

```html+django
{% for advert in adverts %}
    <p>
        <a href="{{ advert.url }}">
            {{ advert.text }}
        </a>
    </p>
{% endfor %}
```

Then, in your own page templates, you can include your snippet template tag with:

```html+django
{% load wagtailcore_tags demo_tags %}

...

{% block content %}

    ...

    {% adverts %}

{% endblock %}
```

## Binding pages to snippets

In the above example, the list of adverts is a fixed list that is displayed via the custom template tag independent of any other content on the page. This might be what you want for a common panel in a sidebar, but, in another scenario, you might wish to display just one specific instance of a snippet on a particular page. This can be accomplished by defining a foreign key to the snippet model within your page model and adding a {class}`~wagtail.admin.panels.FieldPanel` to the page's `content_panels` list. For example, if you wanted to display a specific advert on a `BookPage` instance:

```python
  # ...
  class BookPage(Page):
      advert = models.ForeignKey(
          'demo.Advert',
          null=True,
          blank=True,
          on_delete=models.SET_NULL,
          related_name='+'
      )

      content_panels = Page.content_panels + [
          FieldPanel('advert'),
          # ...
      ]
```

The snippet could then be accessed within your template as `page.advert`.

To attach multiple adverts to a page, the `FieldPanel` can be placed on an inline child object of `BookPage` rather than on `BookPage` itself. Here, this child model is named `BookPageAdvertPlacement` (so-called because there is one such object for each time that an advert is placed on a BookPage):

```python
from django.db import models

from wagtail.models import Page, Orderable

from modelcluster.fields import ParentalKey

# ...

class BookPageAdvertPlacement(Orderable, models.Model):
    page = ParentalKey('demo.BookPage', on_delete=models.CASCADE, related_name='advert_placements')
    advert = models.ForeignKey('demo.Advert', on_delete=models.CASCADE, related_name='+')

    class Meta(Orderable.Meta):
        verbose_name = "advert placement"
        verbose_name_plural = "advert placements"

    panels = [
        FieldPanel('advert'),
    ]

    def __str__(self):
        return self.page.title + " -> " + self.advert.text


class BookPage(Page):
    # ...

    content_panels = Page.content_panels + [
        InlinePanel('advert_placements', label="Adverts"),
        # ...
    ]
```

These child objects are now accessible through the page's `advert_placements` property, and from there we can access the linked `Advert` snippet as `advert`. In the template for `BookPage`, we could include the following:

```html+django
{% for advert_placement in page.advert_placements.all %}
    <p>
        <a href="{{ advert_placement.advert.url }}">
            {{ advert_placement.advert.text }}
        </a>
    </p>
{% endfor %}
```
