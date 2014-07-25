====================
Building your models
====================

If you're not already familiar with Django models, we recommend that you read the Django models documentation first. LINK TO DJANGO DOCS

Wagtail page types are Django models that inherit from the ``wagtail.wagtailcore.models.Page`` model.

In this tutorial we will use the Wagtail project template to create a simple website with a blog.

.. contents:: Contents
    :local:


Adding a body text field to HomePage
====================================

The project template comes with a ``HomePage`` model in the "core" app, but it doesn't contain any content fields. Lets create ``RichText`` field to add a body text to the HomePage:

.. code-block:: python

    # core/models.py

    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailcore.fields import RichTextField


    class HomePage(Page):
        body = RichTextField()

    # Add a FieldPanel for the new panel to display in the admin
    HomePage.content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]


.. topic:: Using South migrations

    When you change your models, run ``dj schemamigration --auto core`` to create a migration file. These migrations are stored in the migrations folder for each app. To apply migrations, run ``dj migrate``.

    See: LINK TO SOUTH DOCS for more information about South


Adding the field to the template
--------------------------------

The homepage template is located at ``core/templates/core/home_page.html``. We will go into the templatetags Wagtail provides further in the next tutorial. But for now, add the following code into the template:

 .. code-block:: django

    # Under the {% extends %} tag
    {% load wagtailcore_tags %}

    # In the content block
    {{ self.body|richtext }}


To test, edit the homepage in the admin, add some content into the "body" field and click "Publish". Then open up the homepage in your browser and you should see the content you've added.


Adding a blog
=============

Lets add a blog to this project. We need to create two new page types, ``BlogIndexPage`` and ``BlogEntryPage``:

.. code-block:: python

    # core/models.py

    from wagtail.wagtailadmin.edit_handlers import FieldPanel
    from wagtail.wagtailcore.fields import RichTextField


    class BlogIndexpage(Page):
        def get_context(self, request):
            # Add list of blog entries to template context
            context = super(BlogIndexPage, self).get_context(request)
            context['blog_entries'] = BlogEntryPage.objects.live().child_of(self)
            return context


    class BlogEntryPage(Page):
        posted_at = models.DateTimeField(auto_now_add=True, editable=False)
        body = RichTextField()

    BlogEntryPage.content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]


After performing the migrations, go into the admin and click "Add subpage" on the HomePage. The BlogIndexPage you have created should be listed as an option. Create a BlogIndexPage, set the title to "Blog" and publish it.


Creating the templates
----------------------

By default, templates in Wagtail are named after the model with camelcase converted to underscores. For the above page types, Wagtail will look for the templates ``core/blog_index_page.html`` and ``core/blog_entry_page.html`` respectively.

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


Using PageChooserPanel
======================



Tagging
=======

Wagtail supports ``django-taggit``

TODO:

 - Adding new models and fields
 - Mention that all page types are Django models and support all fields and features they do
 - Include basic field types, RichTextFields and page choosers
 - Tagging (not needed)
 - Link to djangos model documentation
 - Migrating (mention south very briefly. This is not a south tutorial though)
 - Configuring FieldPanels
 - Configuring SearchFields (not needed)

