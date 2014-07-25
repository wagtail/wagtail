============================
Images, Documents and Embeds
============================


Adding Image and Document fields
================================

Lets add an image and document fields to ``BlogEntryPage``:


.. code-block:: python

    # core/models.py

    from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
    from wagtail.wagtaildocs.edit_handlers import DocumenthooserPanel

    class BlogEntryPage(Page):
        image = models.ForeignKey(
            'wagtailimages.Image',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )
        document = models.ForeignKey(
            'wagtaildocs.Document',
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )

    BlogEntryPage.content_panels = Page.content_panels + [
        ...
        ImageChooserPanel('image'),
        DocumentChooserPanel('document'),
    ]


.. warning::

    You must add ``null=True`` and ``on_delete=models.SET_NULL`` on all ``ForeignKey`` fields that are on a model which inherits from ``Page``

    This is to prevent pages being deleted through cascades which can cause your tree to get corrupted.


Displaying images in templates
==============================


.. topic:: Renditions

    A bit about renditions here

TODO:

 - Linking to images and documents from models and creating choosers
 - A warning about delete cascades
 - Using the {% image %} tag (don't go into too much detail, link to the image tag docs)
 - Mention renditions (but link to Images docs for bigger explanation)
 - Linking to documents from the frontend
 - Using the |embed filter

