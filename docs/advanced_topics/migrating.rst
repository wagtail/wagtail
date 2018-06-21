.. _creating_migrating_pages:

============================
Creating and migrating pages
============================

When performing initial migrations of existing content to Wagtail or when doing Django data migrations of existing Wagtail content we have to manipulate Wagtail :class:`~wagtail.core.models.Page` and :class:`~wagtail.core.models.PageRevision` objects programmatically. 

Creating new pages
==================

Imagine we have a new ``BlogPage`` similar to the one below and we want to migrate existing blog content into our new Wagtail blog. 

.. code-block:: python

    # models.py

    from wagtail.core.fields import RichTextField
    from wagtail.core.models import Page

    class BlogPage(Page):

        body = RichTextField()
        # Other relevant blog fields

We can create new blog posts like we would with any `Django model <https://docs.djangoproject.com/en/stable/intro/tutorial02/#playing-with-the-api>`_:

.. code-block:: python

    post = BlogPage()
    post.body = source_post['body']
    # Fill in other blog fields from the source post
 
    
If we need to backdate our new objects we can do so by setting the :class:`~wagtail.core.models.Page.first_published_at` and :class:`~wagtail.core.models.Page.last_published_at` date/time fields that all Wagtail pages have, but that are not exposed in the admin UI:

.. code-block:: python

    post.first_published_at = source_post['first_published_at']
    post.latest_revision_created_at = source_post['last_revision_created_at']


Before we can save the page, however, we need to save our changes to a new :class:`~wagtail.core.models.PageRevision` object. Revisions are representations of a page at a specific point in time. Every edit of a Wagtail page in the admin creates a new revision when it is saved. 

.. code-block:: python
    
    revision = post.save_revision()
    post.save()

Once the revision and post are saved, the revision can be published.

.. code-block:: python

    revision.publish()

Migrating pages and revisions
=============================

When making changes to a Wagtail page's field schema we sometimes have to change the data for those fields on any pages that exist already in the database. See the  `Django data migrations documentation <https://docs.djangoproject.com/en/stable/topics/migrations/#data-migrations>`_ for a detailed description of how data migrations work. Data migrations are straight-forward for :class:`~wagtail.core.models.Page` objects themselves, but pages also have historical revisions and potentially draft revisions and each of these :class:`~wagtail.core.models.PageRevision` objects also need to be migration.

Modifying page revisions
------------------------

:class:`~wagtail.core.models.PageRevision` objects store the :class:`~wagtail.core.models.Page` object at the time the revision was created as a JSON string in :class:`~wagtail.core.models.PageRevision.content_json`. Any modification of the revision has to load this JSON, modify it, and then dump it back to a string to store it. Given a particular ``revision`` object:

.. code-block:: python

    import json

    # Load the revision content JSON
    revision_content = json.loads(revision.content_json)
    # Migrate the revision content
    revision_content['combined_field'] =  ' '.join(
        revision_content['first_field'], 
        revision_content['last_field']
    )
    # Dump the revision back to JSON and store it
    revision.content_json = json.dumps(revision_content)

Creating the data migration
---------------------------

Knowing that we need to modify both the page objects and the page revision objects, we have to get both models from the `Django app registry <https://docs.djangoproject.com/en/stable/ref/applications/>`_. From there we can loop over all the page objects and modify them as necessary, and then loop over each of the page objects' revision and modify them as described above.

.. code-block:: python

    from django.db import migrations


    def combine_fields(apps, schema_editor):
        # Get the page and revision models
        page_model = apps.get_model('myapp', 'PageModel')
        revision_model = apps.get_model('wagtailcore.PageRevision')

        for page in page_model.objects.all():
            # Migrate the page object
            page.combined_field = ' '.join(page.first_field, page.last_field)

            revisions = revision_model.objects.filter(page=page)
            for revision in revisions:
                # Load the revision content JSON
                revision_content = json.loads(revision.content_json)
                # Migrate the revision content
                revision_content['combined_field'] =  ' '.join(
                    revision_content['first_field'], 
                    revision_content['last_field']
                )
                # Dump the revision back to JSON and store it
                revision.content_json = json.dumps(revision_content)


    class Migration(migrations.Migration):
        dependencies = [
            ('yourappname', '0001_initial'),
        ]

        operations = [
            migrations.RunPython(combine_fields)
        ]

The ``combine_field`` function here serves as a forward data migration. If we want to preserve the ability to go backward, we can write a separate function that will pull apart the fields and pass that as the second argument to ``migrations.RunPython()``, per the `Django data migration documentation <https://docs.djangoproject.com/en/stable/topics/migrations/#data-migrations>`_.
