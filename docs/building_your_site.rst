Building your site
==================

Wagtail manages content internally as a tree of pages. Each node in the tree is an instance of a Django model which subclasses the Wagtail ``Page`` class. You define the structure and interrelationships of your Wagtail site by coding these models and then publishing pages which use the models through the Wagtail admin interface.


The Page Class
~~~~~~~~~~~~~~

``Page`` uses Django's model interface, so you can include any field type and field options that Django allows. Wagtail provides some fields and editing handlers that simplify data entry in the Wagtail admin interface, so you may want to keep those in mind when deciding what properties to add to your models in addition to those already provided by ``Page``.


Built-in Properties of the Page Class
-------------------------------------

Wagtail provides some properties in the ``Page`` class which are common to most webpages. Since you'll be subclassing ``Page``, you don't have to worry about implementing them.

Public Properties
`````````````````

  ``title`` (string, required)
    Human-readable title for the content

  ``slug`` (string, required)
    Machine-readable URL component for this piece of content. The name of the page as it will appear in URLs e.g ``http://domain.com/blog/[my-slug]/``

  ``seo_title`` (string)
    Alternate SEO-crafted title which overrides the normal title for use in the ``<head>`` of a page

  ``search_description`` (string)
    A SEO-crafted description of the content, used in both internal search indexing and for the meta description read by search engines

The ``Page`` class actually has alot more to it, but these are probably the only built-in properties you'll need to worry about when creating templates for your models.


Anatomy of a Wagtail Model
~~~~~~~~~~~~~~~~~~~~~~~~~~

So what does a Wagtail model definition look like?











Introduction to Trees
---------------------

If you're unfamiliar with trees as an abstract data type, you might want to `review the concepts involved. <http://en.wikipedia.org/wiki/Tree_(data_structure)>`_

As a web developer, though, you probably already have a good understanding of trees as filesystem directories or paths. Wagtail pages can create the same structure, as each page in the tree has its own URL path, like so::

  /
    people/
      nien-nunb/
      laura-roslin/
    events/
      captain-picard-day/
      winter-wrap-up/

The Wagtail admin interface uses the tree to organize content for editing, letting you navigate up and down levels in the tree through its Explorer menu. This method of organization is a good place to start in thinking about your own Wagtail models.


Nodes and Leaves
----------------

It might be handy to think of the ``Page``-derived models you want to create as being one of two node types: parents and leaves. Wagtail isn't prescriptive in this approach, but it's a good place to start if you're not experienced in structuring your own content types.

Nodes
`````
Parent nodes on the Wagtail tree probably want to organize and display a browsable index of their descendents. A blog, for instance, needs a way to show a list of individual posts.

A Parent node could provide its own function returning its descendant objects.

.. code-block:: python

  class EventPageIndex(Page):
    ...
    def events(self):
      # Get list of event pages that are descendants of this page
      events = EventPage.objects.filter(
        live=True,
        path__startswith=self.path
      )
      return events

This example makes sure to limit the returned objects to pieces of content which make sense, specifically ones which have been published through Wagtail's admin interface (``live=True``) and are descendants of this node. Wagtail will allow the "illogical" placement of child nodes under a parent, so it's necessary for a parent model to index only those children which make sense.

Leaves
``````
Leaves are the pieces of content itself, a page which is consumable, and might just consist of a bunch of properties. A blog page leaf might have some body text and an image. A person page leaf might have a photo, a name, and an address.

It might be helpful for a leaf to provide a way to back up along the tree to a parent, such as in the case of breadcrumbs navigation. The tree might also be deep enough that a leaf's parent won't be included in general site navigation.

The model for the leaf could provide a function that traverses the tree in the opposite direction and returns an appropriate ancestor:

.. code-block:: python

  class BlogPage(Page):
    ...
    def blog_index(self):
      # Find blog index in ancestors
      for ancestor in reversed(self.get_ancestors()):
        if isinstance(ancestor.specific, BlogIndexPage):
          return ancestor

      # No ancestors are blog indexes, just return first blog index in database
      return BlogIndexPage.objects.first()

Since Wagtail doesn't limit what Page-derived classes can be assigned as parents and children, the reverse tree traversal needs to accommodate cases which might not be expected, such as the lack of a "logical" parent to a leaf.

Other Relationships
```````````````````
Your ``Page``-derived models might have other interrelationships which extend the basic Wagtail tree or depart from it entirely. You could provide functions to navigate between siblings, such as a "Next Post" link on a blog page (``post->post->post``). It might make sense for subtrees to interrelate, such as in a discussion forum (``forum->post->replies``) Skipping across the hierarchy might make sense, too, as all objects of a certain model class might interrelate regardless of their ancestors (``events = EventPage.objects.all``). Since there's no restriction on the combination of model classes that can be used at any point in the tree, and it's largely up to the models to define their interrelations, the possibilities are really endless.


Model Recipes
~~~~~~~~~~~~~

Overriding the serve() Method
-----------------------------

Wagtail defaults to serving ``Page``-derived models by passing ``self`` to a Django HTML template matching the model's name, but suppose you wanted to serve something other than HTML? You can override the ``serve()`` method provided by the ``Page`` class and handle the Django request and response more directly.

Consider this example from the Wagtail demo site's ``models.py``, which serves an ``EventPage`` object as an iCal file if the ``format`` variable is set in the request:

.. code-block:: python

  class EventPage(Page):
    ...
    def serve(self, request):
      if "format" in request.GET:
        if request.GET['format'] == 'ical':
          # Export to ical format
          response = HttpResponse(
            export_event(self, 'ical'),
            content_type='text/calendar',
          )
          response['Content-Disposition'] = 'attachment; filename=' + self.slug + '.ics'
          return response
        else:
          # Unrecognised format error
          message = 'Could not export event\n\nUnrecognised format: ' + request.GET['format']
          return HttpResponse(message, content_type='text/plain')
      else:
        # Display event page as usual
        return super(EventPage, self).serve(request)

``serve()`` takes a Django request object and returns a Django response object. Wagtail returns a ``TemplateResponse`` object with the template and context which it generates, which allows middleware to function as intended, so keep in mind that a simpler response object like a ``HttpResponse`` will not receive these benefits.

With this strategy, you could use Django or Python utilities to render your model in JSON or XML or any other format you'd like.


Adding Endpoints with Custom route() Methods
--------------------------------------------

Wagtail routes requests by iterating over the path components (separated with a forward slash ``/``), finding matching objects based on their slug, and delegating further routing to that object's model class. The Wagtail source is very instructive in figuring out what's happening. This is the default ``route()`` method of the ``Page`` class:

.. code-block:: python

  class Page(...):

    ...

    def route(self, request, path_components):
      if path_components:
        # request is for a child of this page
        child_slug = path_components[0]
        remaining_components = path_components[1:]

        # find a matching child or 404
        try:
          subpage = self.get_children().get(slug=child_slug)
        except Page.DoesNotExist:
          raise Http404

        # delegate further routing
        return subpage.specific.route(request, remaining_components)

      else:
        # request is for this very page
        if self.live:
          # use the serve() method to render the request if the page is published
          return self.serve(request)
        else:
          # the page matches the request, but isn't published, so 404
          raise Http404

The contract is pretty simple. ``route()`` takes the current object (``self``), the ``request`` object, and a list of the remaining ``path_components`` from the request URL. It either continues delegating routing by calling ``route()`` again on one of its children in the Wagtail tree, or ends the routing process by serving something -- either normally through the ``self.serve()`` method or by raising a 404 error.

By overriding the ``route()`` method, we could create custom endpoints for each object in the Wagtail tree. One use case might be using an alternate template when encountering the ``print/`` endpoint in the path. Another might be a REST API which interacts with the current object. Just to see what's involved, lets make a simple model which prints out all of its child path components.

First, ``models.py``:

.. code-block:: python

  from django.shortcuts import render

  ...

  class Echoer(Page):
  
    def route(self, request, path_components):
      if path_components:
        return render(request, self.template, {
          'self': self,
          'echo': ' '.join(path_components),
        })
      else:
        if self.live:
          return self.serve(request)
        else:
          raise Http404

  Echoer.content_panels = [
    FieldPanel('title', classname="full title"),
  ]

  Echoer.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
  ]

This model, ``Echoer``, doesn't define any properties, but does subclass ``Page`` so objects will be able to have a custom title and slug. The template just has to display our ``{{ echo }}`` property. We're skipping the ``serve()`` method entirely, but you could include your render code there to stay consistent with Wagtail's conventions.

Now, once creating a new ``Echoer`` page in the Wagtail admin titled "Echo Base," requests such as::

  http://127.0.0.1:8000/echo-base/tauntaun/kennel/bed/and/breakfast/

Will return::

  tauntaun kennel bed and breakfast

Lovely, huh? (We know.)



Tagging
-------

Wagtail provides tagging capability through the combination of two django modules, ``taggit`` and ``modelcluster``. ``taggit`` provides a model for tags which is extended by ``modelcluster``, which in turn provides some magical database abstraction which makes drafts and revisions possible in Wagtail. It's a tricky recipe, but the net effect is a many-to-many relationship between your model and a tag class reserved for your model.

Using an example from the Wagtail demo site, here's what the tag model and the relationship field looks like in ``models.py``:

.. code-block:: python

  from modelcluster.fields import ParentalKey
  from modelcluster.tags import ClusterTaggableManager
  from taggit.models import Tag, TaggedItemBase
  ...
  class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('demo.BlogPage', related_name='tagged_items')
  ...
  class BlogPage(Page):
    ...
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

  BlogPage.promote_panels = [
    ...
    FieldPanel('tags'),
  ]

Wagtail's admin provides a nice interface for inputting tags into your content, with typeahead tag completion and friendly tag icons.

Now that we have the many-to-many tag relationship in place, we can fit in a way to render both sides of the relation. Here's more of the Wagtail demo site ``models.py``, where the index model for ``BlogPage`` is extended with logic for filtering the index by tag:

.. code-block:: python

  class BlogIndexPage(Page):
    ...
    def serve(self, request):
      # Get blogs
      blogs = self.blogs

      # Filter by tag
      tag = request.GET.get('tag')
      if tag:
        blogs = blogs.filter(tags__name=tag)

      return render(request, self.template, {
        'self': self,
        'blogs': blogs,
      })

Here, ``blogs.filter(tags__name=tag)`` invokes a reverse Django queryset filter on the ``BlogPageTag`` model to optionally limit the ``BlogPage`` objects sent to the template for rendering. Now, lets render both sides of the relation by showing the tags associated with an object and a way of showing all of the objects associated with each tag. This could be added to the ``blog_page.html`` template:

.. code-block:: django

  {% for tag in self.tags.all %}
    <a href="{% pageurl self.blog_index %}?tag={{ tag }}">{{ tag }}</a>
  {% endfor %}

Iterating through ``self.tags.all`` will display each tag associated with ``self``, while the link(s) back to the index make use of the filter option added to the ``BlogIndexPage`` model. A Django query could also use the ``tagged_items`` related name field to get ``BlogPage`` objects associated with a tag.

This is just one possible way of creating a taxonomy for Wagtail objects. With all of the components for a taxonomy available through Wagtail, you should be able to fulfill even the most exotic taxonomic schemes.





Extended Page Data with ParentalKey
-----------------------------------




Templates
~~~~~~~~~

Location
--------

For each of your ``Page``-derived models, Wagtail will look for a template in the following location, relative to your project root::

  project/
    app/
      templates/
        app/
          blog_index_page.html
      models.py

Class names are converted from camel case to underscores. For example, the template for model class ``BlogIndexPage`` would be assumed to be ``blog_index_page.html``. 

Self
----

By default, the context passed to a model's template consists of two properties: ``self`` and ``request``. ``self`` is the model object being displayed. ``request`` is the normal Django request object.


Template Tags
-------------

  **pageurl**

    Takes a ``Page``-derived object and returns its URL as relative (``/foo/bar/``) if it's within the same site as the current page, or absolute (``http://example.com/foo/bar/``) if not.

    .. code-block:: django

      {% load pageurl %}
      ...
      <a href="{% pageurl blog %}">

  **slugurl**

    Takes a ``slug`` string and returns the URL for the ``Page``-derived object with that slug. Like ``pageurl``, will try to provide a relative link if possible, but will default to an absolute link if on a different site.

    .. code-block:: django

      {% load slugurl %}
      ...
      <a href="{% slugurl blogslug %}">
    
  **wagtailuserbar**

    This tag provides a Wagtail icon and flyout menu on the top-right of a page for a logged-in user with editing capabilities, with the option of editing the current Page-derived object or adding a new sibling object.

    .. code-block:: django

      {% load wagtailuserbar %}
      ...
      {% wagtailuserbar %}
  
  **image**

    This template tag provides a way to process an image with a method and dimensions.

    .. code-block:: django
    
      {% load image_tags %}
      ...
      {% image self.photo max-320x200 %}
      or
      {% image self.photo max-320x200 as img %}
  
      'max': 'resize_to_max',
      'min': 'resize_to_min',
      'width': 'resize_to_width',
      'height': 'resize_to_height',
      'fill': 'resize_to_fill',


Template Filters
----------------

  **rich_text**

    This filter is required for use with any ``RichTextField``. It will expand internal shorthand references to embeds and links made in the Wagtail editor into fully-baked HTML ready for display. **Note that the template tag loaded differs from the name of the filter.**

    .. code-block:: django

      {% load rich_text %}
      ...
      {{ body|richtext }}



Site
~~~~

Django's built-in admin interface provides the way to map a "site" (hostname or domain) to any node in the wagtail tree, using that node as the site's root.

Access this by going to ``/django-admin/`` and then "Home › Wagtailcore › Sites." To try out a development site, add a single site with the hostname ``localhost`` at port ``8000`` and map it to one of the pieces of content you have created.

Wagtail's developers plan to move the site settings into the Wagtail admin interface.



Example Site
~~~~~~~~~~~~

Serafeim Papastefanos has written a comprehensive tutorial on creating a site from scratch in Wagtail; for the time being, this is our recommended resource:

`spapas.github.io/2014/02/13/wagtail-tutorial/ <http://spapas.github.io/2014/02/13/wagtail-tutorial/>`_
