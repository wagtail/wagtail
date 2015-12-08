
.. _snippets:

Snippets
========

Snippets are pieces of content which do not necessitate a full webpage to render. They could be used for making secondary content, such as headers, footers, and sidebars, editable in the Wagtail admin. Snippets are models which do not inherit the ``Page`` class and are thus not organized into the Wagtail tree, but can still be made editable by assigning panels and identifying the model as a snippet with the ``register_snippet`` class decorator.

Snippets lack many of the features of pages, such as being orderable in the Wagtail admin or having a defined URL, so decide carefully if the content type you would want to build into a snippet might be more suited to a page.

Snippet Models
--------------

Here's an example snippet from the Wagtail demo website:

.. code-block:: python

  from django.db import models

  from wagtail.wagtailadmin.edit_handlers import FieldPanel
  from wagtail.wagtailsnippets.models import register_snippet

  ...

  @register_snippet
  class Advert(models.Model):
      url = models.URLField(null=True, blank=True)
      text = models.CharField(max_length=255)
  
      panels = [
          FieldPanel('url'),
          FieldPanel('text'),
      ]
      
      def __str__(self):              # __unicode__ on Python 2
          return self.text

The ``Advert`` model uses the basic Django model class and defines two properties: text and URL. The editing interface is very close to that provided for ``Page``-derived models, with fields assigned in the panels property. Snippets do not use multiple tabs of fields, nor do they provide the "save as draft" or "submit for moderation" features.

``@register_snippet`` tells Wagtail to treat the model as a snippet. The ``panels`` list defines the fields to show on the snippet editing page. It's also important to provide a string representation of the class through ``def __str__(self):`` so that the snippet objects make sense when listed in the Wagtail admin.

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

.. code-block:: html+django

  {% for advert in adverts %}
    <p>
      <a href="{{ advert.url }}">
        {{ advert.text }}
      </a>
    </p>
  {% endfor %}

Then in your own page templates, you can include your snippet template tag with:

.. code-block:: html+django

  {% load wagtailcore_tags demo_tags %}

  ...

  {% block content %}
  
    ...

    {% adverts %}

  {% endblock %}


Binding Pages to Snippets
-------------------------

In the above example, the list of adverts is a fixed list, displayed as part of the template independently of the page content. This might be what you want for a common panel in a sidebar, say - but in other scenarios you may wish to refer to a snippet within page content. This can be done by defining a foreign key to the snippet model within your page model, and adding a ``SnippetChooserPanel`` to the page's ``content_panels`` definitions. For example, if you wanted to be able to specify an advert to appear on ``BookPage``:

.. code-block:: python

  from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
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
          SnippetChooserPanel('advert'),
          # ...
      ]


The snippet could then be accessed within your template as ``page.advert``.

To attach multiple adverts to a page, the ``SnippetChooserPanel`` can be placed on an inline child object of ``BookPage``, rather than on ``BookPage`` itself. Here this child model is named ``BookPageAdvertPlacement`` (so called because there is one such object for each time that an advert is placed on a BookPage):


.. code-block:: python

  from django.db import models

  from wagtail.wagtailcore.models import Page, Orderable
  from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

  from modelcluster.fields import ParentalKey
  
  ...

  class BookPageAdvertPlacement(Orderable, models.Model):
      page = ParentalKey('demo.BookPage', related_name='advert_placements')
      advert = models.ForeignKey('demo.Advert', related_name='+')
  
      class Meta:
          verbose_name = "advert placement"
          verbose_name_plural = "advert placements"
  
      panels = [
          SnippetChooserPanel('advert'),
      ]
  
      def __str__(self):              # __unicode__ on Python 2
          return self.page.title + " -> " + self.advert.text
  
  
  class BookPage(Page):
      ...
  
      content_panels = Page.content_panels + [
          InlinePanel('advert_placements', label="Adverts"),
          # ...
      ]



These child objects are now accessible through the page's ``advert_placements`` property, and from there we can access the linked Advert snippet as ``advert``. In the template for ``BookPage``, we could include the following:

.. code-block:: html+django

  {% for advert_placement in page.advert_placements.all %}
    <p><a href="{{ advert_placement.advert.url }}">{{ advert_placement.advert.text }}</a></p>
  {% endfor %}


.. _wagtailsnippets_making_snippets_searchable:

Making Snippets Searchable
--------------------------

If a snippet model inherits from ``wagtail.wagtailsearch.index.Indexed``, as described in :ref:`wagtailsearch_indexing_models`, Wagtail will automatically add a search box to the chooser interface for that snippet type. For example, the ``Advert`` snippet could be made searchable as follows:

.. code-block:: python

  ...

  from wagtail.wagtailsearch import index

  ...

  @register_snippet
  class Advert(models.Model, index.Indexed):
      url = models.URLField(null=True, blank=True)
      text = models.CharField(max_length=255)

      panels = [
          FieldPanel('url'),
          FieldPanel('text'),
      ]

      search_fields = [
          index.SearchField('text', partial_match=True),
      ]


Tagging snippets
----------------

Adding tags to snippets is very similar to adding tags to pages. The only difference is that :class:`taggit.manager.TaggableManager` should be used in the place of :class:`~modelcluster.contrib.taggit.ClusterTaggableManager`.

.. code-block:: python

    from modelcluster.fields import ParentalKey
    from taggit.models import TaggedItemBase
    from taggit.managers import TaggableManager

    class AdvertTag(TaggedItemBase):
        content_object = ParentalKey('demo.Advert', related_name='tagged_items')

    @register_snippet
    class Advert(models.Model):
        ...
        tags = TaggableManager(through=BlogPageTag, blank=True)

        panels = [
            ...
            FieldPanel('tags'),
        ]

The :ref:`documentation on tagging pages <tagging>` has more information on how to use tags in views.
