
.. _model_recipes:

Model Recipes
=============

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


Custom Page Contexts by Overriding get_context()
------------------------------------------------



Load Alternate Templates by Overriding get_template()
-----------------------------------------------------



Page Modes
----------

get_page_modes
show_as_mode




