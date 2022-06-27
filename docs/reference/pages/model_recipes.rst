
.. _page_model_recipes:

Recipes
=======

Overriding the :meth:`~wagtail.models.Page.serve` Method
--------------------------------------------------------------------

Wagtail defaults to serving :class:`~wagtail.models.Page`-derived models by passing a reference to the page object to a Django HTML template matching the model's name, but suppose you wanted to serve something other than HTML? You can override the :meth:`~wagtail.models.Page.serve` method provided by the :class:`~wagtail.models.Page` class and handle the Django request and response more directly.

Consider this example of an ``EventPage`` object which is served as an iCal file if the ``format`` variable is set in the request:

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
                return super().serve(request)

:meth:`~wagtail.models.Page.serve` takes a Django request object and returns a Django response object. Wagtail returns a ``TemplateResponse`` object with the template and context which it generates, which allows middleware to function as intended, so keep in mind that a simpler response object like a ``HttpResponse`` will not receive these benefits.

With this strategy, you could use Django or Python utilities to render your model in JSON or XML or any other format you'd like.


.. _overriding_route_method:

Adding Endpoints with Custom :meth:`~wagtail.models.Page.route` Methods
-----------------------------------------------------------------------------------

.. note::

    A much simpler way of adding more endpoints to pages is provided by the :mod:`~wagtail.contrib.routable_page` module.

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
                    # Return a RouteResult that will tell Wagtail to call
                    # this page's serve() method
                    return RouteResult(self)
                else:
                    # the page matches the request, but isn't published, so 404
                    raise Http404

:meth:`~wagtail.models.Page.route` takes the current object (``self``), the ``request`` object, and a list of the remaining ``path_components`` from the request URL. It either continues delegating routing by calling :meth:`~wagtail.models.Page.route` again on one of its children in the Wagtail tree, or ends the routing process by returning a ``RouteResult`` object or raising a 404 error.

The ``RouteResult`` object (defined in wagtail.url_routing) encapsulates all the information Wagtail needs to call a page's :meth:`~wagtail.models.Page.serve` method and return a final response: this information consists of the page object, and any additional ``args``/``kwargs`` to be passed to :meth:`~wagtail.models.Page.serve`.

By overriding the :meth:`~wagtail.models.Page.route` method, we could create custom endpoints for each object in the Wagtail tree. One use case might be using an alternate template when encountering the ``print/`` endpoint in the path. Another might be a REST API which interacts with the current object. Just to see what's involved, lets make a simple model which prints out all of its child path components.

First, ``models.py``:

.. code-block:: python

    from django.shortcuts import render
    from wagtail.url_routing import RouteResult
    from django.http.response import Http404
    from wagtail.models import Page

    ...

    class Echoer(Page):

        def route(self, request, path_components):
            if path_components:
                # tell Wagtail to call self.serve() with an additional 'path_components' kwarg
                return RouteResult(self, kwargs={'path_components': path_components})
            else:
                if self.live:
                    # tell Wagtail to call self.serve() with no further args
                    return RouteResult(self)
                else:
                    raise Http404

        def serve(self, path_components=[]):
            return render(request, self.template, {
                'page': self,
                'echo': ' '.join(path_components),
            })


This model, ``Echoer``, doesn't define any properties, but does subclass ``Page`` so objects will be able to have a custom title and slug. The template just has to display our ``{{ echo }}`` property.

Now, once creating a new ``Echoer`` page in the Wagtail admin titled "Echo Base," requests such as::

    http://127.0.0.1:8000/echo-base/tauntaun/kennel/bed/and/breakfast/

Will return::

    tauntaun kennel bed and breakfast

Be careful if you're introducing new required arguments to the ``serve()`` method - Wagtail still needs to be able to display a default view of the page for previewing and moderation, and by default will attempt to do this by calling ``serve()`` with a request object and no further arguments. If your ``serve()`` method does not accept that as a method signature, you will need to override the page's ``serve_preview()`` method to call ``serve()`` with suitable arguments:

.. code-block:: python

    def serve_preview(self, request, mode_name):
        return self.serve(request, variant='radiant')

.. _tagging:

Tagging
-------

Wagtail provides tagging capabilities through the combination of two Django modules, `django-taggit <https://django-taggit.readthedocs.io/>`_ (which provides a general-purpose tagging implementation) and `django-modelcluster <https://github.com/wagtail/django-modelcluster>`_ (which extends django-taggit's ``TaggableManager`` to allow tag relations to be managed in memory without writing to the database - necessary for handling previews and revisions). To add tagging to a page model, you'll need to define a 'through' model inheriting from ``TaggedItemBase`` to set up the many-to-many relationship between django-taggit's ``Tag`` model and your page model, and add a ``ClusterTaggableManager`` accessor to your page model to present this relation as a single tag field.

In this example, we set up tagging on ``BlogPage`` through a ``BlogPageTag`` model:

.. code-block:: python

    # models.py

    from modelcluster.fields import ParentalKey
    from modelcluster.contrib.taggit import ClusterTaggableManager
    from taggit.models import TaggedItemBase

    class BlogPageTag(TaggedItemBase):
        content_object = ParentalKey('demo.BlogPage', on_delete=models.CASCADE, related_name='tagged_items')

    class BlogPage(Page):
        ...
        tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

        promote_panels = Page.promote_panels + [
            ...
            FieldPanel('tags'),
        ]

Wagtail's admin provides a nice interface for inputting tags into your content, with typeahead tag completion and friendly tag icons.

We can now make use of the many-to-many tag relationship in our views and templates. For example, we can set up the blog's index page to accept a ``?tag=...`` query parameter to filter the ``BlogPage`` listing by tag:

.. code-block:: python

    from django.shortcuts import render

    class BlogIndexPage(Page):
        ...
        def get_context(self, request):
            context = super().get_context(request)

            # Get blog entries
            blog_entries = BlogPage.objects.child_of(self).live()

            # Filter by tag
            tag = request.GET.get('tag')
            if tag:
                blog_entries = blog_entries.filter(tags__name=tag)

            context['blog_entries'] = blog_entries
            return context


Here, ``blog_entries.filter(tags__name=tag)`` follows the ``tags`` relation on ``BlogPage``, to filter the listing to only those pages with a matching tag name before passing this to the template for rendering. We can now update the ``blog_page.html`` template to show a list of tags associated with the page, with links back to the filtered index page:

.. code-block:: html+django

    {% for tag in page.tags.all %}
        <a href="{% pageurl page.blog_index %}?tag={{ tag }}">{{ tag }}</a>
    {% endfor %}

Iterating through ``page.tags.all`` will display each tag associated with ``page``, while the links back to the index make use of the filter option added to the ``BlogIndexPage`` model. A Django query could also use the ``tagged_items`` related name field to get ``BlogPage`` objects associated with a tag.

The same approach can be used to add tagging to non-page models managed through :ref:`snippets` and :doc:`/reference/contrib/modeladmin/index`. In this case, the model must inherit from ``modelcluster.models.ClusterableModel`` to be compatible with ``ClusterTaggableManager``.


Custom tag models
-----------------

In the above example, any newly-created tags will be added to django-taggit's default ``Tag`` model, which will be shared by all other models using the same recipe as well as Wagtail's image and document models. In particular, this means that the autocompletion suggestions on tag fields will include tags previously added to other models. To avoid this, you can set up a custom tag model inheriting from ``TagBase``, along with a 'through' model inheriting from ``ItemBase``, which will provide an independent pool of tags for that page model.

.. code-block:: python

    from django.db import models
    from modelcluster.contrib.taggit import ClusterTaggableManager
    from modelcluster.fields import ParentalKey
    from taggit.models import TagBase, ItemBase

    class BlogTag(TagBase):
        class Meta:
            verbose_name = "blog tag"
            verbose_name_plural = "blog tags"


    class TaggedBlog(ItemBase):
        tag = models.ForeignKey(
            BlogTag, related_name="tagged_blogs", on_delete=models.CASCADE
        )
        content_object = ParentalKey(
            to='demo.BlogPage',
            on_delete=models.CASCADE,
            related_name='tagged_items'
        )

    class BlogPage(Page):
        ...
        tags = ClusterTaggableManager(through='demo.TaggedBlog', blank=True)

Within the admin, the tag field will automatically recognise the custom tag model being used, and will offer autocomplete suggestions taken from that tag model.


Disabling free tagging
----------------------

By default, tag fields work on a "free tagging" basis: editors can enter anything into the field, and upon saving, any tag text not recognised as an existing tag will be created automatically. To disable this behaviour, and only allow editors to enter tags that already exist in the database, custom tag models accept a ``free_tagging = False`` option:

.. code-block:: python

    from taggit.models import TagBase
    from wagtail.snippets.models import register_snippet

    @register_snippet
    class BlogTag(TagBase):
        free_tagging = False

        class Meta:
            verbose_name = "blog tag"
            verbose_name_plural = "blog tags"

Here we have registered ``BlogTag`` as a snippet, to provide an interface for administrators (and other users with the appropriate permissions) to manage the allowed set of tags. With the ``free_tagging = False`` option set, editors can no longer enter arbitrary text into the tag field, and must instead select existing tags from the autocomplete dropdown.

Managing tags with Wagtail's `ModelAdmin`
-----------------------------------------

In order to manage all the tags used in a project, you can a use the ``ModelAdmin`` to add the ``Tag`` model to the Wagtail admin. This will allow you to have a tag admin interface within the main menu in which you can add, edit or delete your tags.

Tags that are removed from a content don't get deleted from the ``Tag`` model and will still be shown in typeahead tag completion. So having a tag interface is a great way to completely get rid of tags you don't need.

To add the tag interface, add the following block of code to a ``wagtail_hooks.py`` file within any your project’s apps:

.. code-block:: python

    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from wagtail.admin.edit_handlers import FieldPanel
    from taggit.models import Tag


    class TagsModelAdmin(ModelAdmin):
        Tag.panels = [FieldPanel("name")]  # only show the name field
        model = Tag
        menu_label = "Tags"
        menu_icon = "tag"  # change as required
        menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
        list_display = ["name", "slug"]
        search_fields = ("name",)


    modeladmin_register(TagsModelAdmin)


A ``Tag`` model has a ``name`` and ``slug`` required fields. If you decide to add a tag, it is recommended to only display the ``name`` field panel as the slug field is autofilled when the ``name`` field is filled and you don't need to enter the same name in both the fields.
