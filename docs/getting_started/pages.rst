==============
Creating pages
==============

This tutorial assumes that you are already familar with Django models. If not, have a quick look through Django's model documentation here. LINK TO DJANGO DOCS

All page types in Wagtail are Django models that inherit from the ``wagtail.wagtailcore.models.Page`` class. Each page type also has a template which is used when the user browses to a page of that type.

In this tutorial, we will use the project that we created in :doc:`creating_your_project` to create a simple website with a blog.

.. contents:: Contents
    :local:


Adding a body text field to HomePage
====================================

The project template includes a ``HomePage`` model in the "core" app. To begin with, this model doesnt have any content fields so lets create a ``RichText`` field to add some body text to the HomePage:

.. code-block:: python

    # core/models.py

    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailcore.fields import RichTextField


    class HomePage(Page):
        body = RichTextField()

    # Add a FieldPanel for the new field so it displays in the admin interface
    HomePage.content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]


After changing models in your app, don't forget to migrate your database before testing. See LINK TO MIGARTION DOCS for more info.


Adding the field to the template
--------------------------------

The homepage template is located at ``core/templates/core/home_page.html`` (template filenames are automatically inferred from the name of the model).

Wagtail provides a template filter called ``richtext`` which can be found in the ``wagtailcore_tags`` library. This should always be used when displaying content of richtext fields.

 .. code-block:: django

    # Under the {% extends %} tag
    {% load wagtailcore_tags %}

    # In the content block
    {{ self.body|richtext }}


To test, edit the homepage in the admin, add some content into the "body" field then click "Publish". Then open up the homepage in your browser and you should see the content you've added.


Adding a blog
=============

Let's add a blog to this project. We need to create two new page types, ``BlogIndexPage`` and ``BlogEntryPage``:

.. code-block:: python

    # core/models.py

    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailcore.fields import RichTextField


    class BlogIndexPage(Page):
        def get_context(self, request):
            # Add list of blog entries to template context
            context = super(BlogIndexPage, self).get_context(request)
            context['blog_entries'] = BlogEntryPage.objects.live().child_of(self)
            return context


    class BlogEntryPage(Page):
        posted_at = models.DateTimeField(auto_now_add=True, editable=False)
        body = RichTextField()

        # Only allow creating blog entries under blog indexes
        parent_page_types = [BlogIndexPage]

    BlogEntryPage.content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]


After creating and running the migrations, go into the admin and click "Add subpage" on the HomePage. The BlogIndexPage you have created should be listed as an option. Create a BlogIndexPage, set the title to "Blog" and publish it.


Creating the templates
----------------------

By default, templates in Wagtail are named after the model with camelcase letters converted to underscores. For the above page types, Wagtail will look for the templates ``core/blog_index_page.html`` and ``core/blog_entry_page.html`` respectively.

Create both of these templates by copying ``home_page.html`` and clearing out the contents block.

For the blog index, we have overridden the ``get_context`` method to add a list of blog entries to the template context. All pages in Wagtail provide a ``.url`` property to allow finding the URL of the page. Here's a way on how we can use this to create a list of blog entries in the blog index:


 .. code-block:: django

    # core/templates/core/blog_index_page.html

    # In the content block
    <ul class="blog-entries">
        {% for blog_entry in blog_entries %}
            <li><a href="{{ blog_entry.url }}">{{ blog_entry }}</a></li>
        {% endfor %}
    </ul>


Creating menus
==============

Now that the site has multiple pages, lets create some menus to make it easier for the user to navigate.


Main menu
---------

.. code-block:: django

    <header>
        {% with request.site.root_page as home_page %}
            <ul class="menu">
                <li><a href="{{ home_page.url }}">{{ home_page.title }}</a></li>
                {% for menu_item in home_page.get_children.live.in_menu %}
                    <li><a href="{{ menu_item.url }}">{{ menu_item }}</a></li>
                {% endfor %}
            </ul>
        {% endwith %}
    </header>


Breadcrumb
----------


Linking pages together
======================

ForeignKey to another page
PageChooserPanel


Tagging
=======

Wagtail supports ``django-taggit``


Child objects
=============

TODO:

 - What they are how they work, etc (mention modelcluster and what it does, mention page revisions)
 - Creating a child object and linking it to a Page with a ParentalKey
 - InlinePanel

Many to Many relationships
==========================

TODO



TODO
====

 - Adding new models and fields
 - Mention that all page types are Django models and support all fields and features they do
 - Include basic field types, RichTextFields and page choosers
 - Tagging (not needed)
 - Link to djangos model documentation
 - Migrating (mention south very briefly. This is not a south tutorial though)
 - Configuring FieldPanels
 - Configuring SearchFields (not needed)

