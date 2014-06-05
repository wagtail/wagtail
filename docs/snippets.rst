
.. _snippets:

Snippets
========

Snippets are pieces of content which do not necessitate a full webpage to render. They could be used for making secondary content, such as headers, footers, and sidebars, editable in the Wagtail admin. Snippets are models which do not inherit the ``Page`` class and are thus not organized into the Wagtail tree, but can still be made editable by assigning panels and identifying the model as a snippet with ``register_snippet()``.

Snippets are not search-able or order-able in the Wagtail admin, so decide carefully if the content type you would want to build into a snippet might be more suited to a page.

Snippet Models
--------------

Here's an example snippet from the Wagtail demo website:

.. code-block:: python

  from django.db import models

  from wagtail.wagtailadmin.edit_handlers import FieldPanel
  from wagtail.wagtailsnippets.models import register_snippet
  
  ...

  class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
      FieldPanel('url'),
      FieldPanel('text'),
    ]

    def __unicode__(self):
      return self.text

  register_snippet(Advert)

The ``Advert`` model uses the basic Django model class and defines two properties: text and url. The editing interface is very close to that provided for ``Page``-derived models, with fields assigned in the panels property. Snippets do not use multiple tabs of fields, nor do they provide the "save as draft" or "submit for moderation" features.

``register_snippet(Advert)`` tells Wagtail to treat the model as a snippet. The ``panels`` list defines the fields to show on the snippet editing page. It's also important to provide a string representation of the class through ``def __unicode__(self):`` so that the snippet objects make sense when listed in the Wagtail admin.

Including Snippets in Template Tags
-----------------------------------

The simplest way to make your snippets available to templates is with a template tag. This is mostly done with vanilla Django, so perhaps reviewing Django's documentation for `django custom template tags`_ will be more helpful. We'll go over the basics, though, and make note of any considerations to make for Wagtail.

First, add a new python file to a ``templatetags`` folder within your app. The demo website, for instance uses the path ``wagtaildemo/demo/templatetags/demo_tags.py``. We'll need to load some Django modules and our app's models and ready the ``register`` decorator:

.. _django custom template tags: https://docs.djangoproject.com/en/dev/howto/custom-template-tags/

.. code-block:: python

  from django import template
  from demo.models import *

  register = template.Library()

  ...

  # Advert snippets
  @register.inclusion_tag('demo/tags/adverts.html', takes_context=True)
  def adverts(context):
    return {
      'adverts': Advert.objects.all(),
      'request': context['request'],
    }

``@register.inclusion_tag()`` takes two variables: a template and a boolean on whether that template should be passed a request context. It's a good idea to include request contexts in your custom template tags, since some Wagtail-specific template tags like ``pageurl`` need the context to work properly. The template tag function could take arguments and filter the adverts to return a specific model, but for brevity we'll just use ``Advert.objects.all()``.

Here's what's in the template used by the template tag:

.. code-block:: django

  {% for advert in adverts %}
    <p>
      <a href="{{ advert.url }}">
        {{ advert.text }}
      </a>
    </p>
  {% endfor %}

Then in your own page templates, you can include your snippet template tag with:

.. code-block:: django

  {% block content %}
  
    ...

    {% adverts %}

  {% endblock %}

Binding Pages to Snippets
-------------------------

An alternate strategy for including snippets might involve explicitly binding a specific page object to a specific snippet object. Lets add another snippet class to see how that might work:

.. code-block:: python

  from django.db import models

  from wagtail.wagtailcore.models import Page
  from wagtail.wagtailadmin.edit_handlers import PageChooserPanel
  from wagtail.wagtailsnippets.models import register_snippet
  from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

  from modelcluster.fields import ParentalKey
  
  ...

  class AdvertPlacement(models.Model):
    page = ParentalKey('wagtailcore.Page', related_name='advert_placements')
    advert = models.ForeignKey('demo.Advert', related_name='+')

    class Meta:
      verbose_name = "Advert Placement"
      verbose_name_plural = "Advert Placements"

    panels = [
      PageChooserPanel('page'),
      SnippetChooserPanel('advert', Advert),
    ]

    def __unicode__(self):
      return self.page.title + " -> " + self.advert.text

  register_snippet(AdvertPlacement)

The class ``AdvertPlacement`` has two properties, ``page`` and ``advert``, which point to other models. Wagtail provides a ``PageChooserPanel`` and ``SnippetChooserPanel`` to let us make painless selection of those properties in the Wagtail admin. Note also the ``Meta`` class, which you can stock with the ``verbose_name`` and ``verbose_name_plural`` properties to override the snippet labels in the Wagtail admin. The text representation of the class has also gotten fancy, using both properties to construct a compound label showing the relationship it forms between a page and an Advert.

With this snippet in place, we can use the reverse ``related_name`` lookup label ``advert_placements`` to iterate over any placements within our template files. In the template for a ``Page``-derived model, we could include the following:

.. code-block:: django

  {% if self.advert_placements %}
    {% for advert_placement in self.advert_placements.all %}
      <p><a href="{{ advert_placement.advert.url }}">{{ advert_placement.advert.text }}</a></p>
    {% endfor %}
  {% endif %}


