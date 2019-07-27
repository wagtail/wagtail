=====================================
Extra information on exposing the API
=====================================

Images
------

If you have in your model an image you can expose the image by using the ImageRenditionField.
:class:`wagtail.images.api.fields.ImageRenditionField`. The ImageRenditionField will return url, width, height.

..code-block:: python

    class SomePage(Page):
        ...
        image = models.ForeignKey('wagtailimages.Image', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
        ...

        @property
        def img(self):
            return ImageRenditionField('width-700').to_representation(self.image)

        @property
        def alt(self):
            return self.image.title

        api_fields = [
            ...
            APIField('img'),
            APIField('alt'),
            ...
        ]

Alterantive you also can do the following

..code-block:: python

        api_field = [
            APIField('image', serializer=ImageRenditionField('fill-300x300'))
        ]

If the name "image" is different as the can add the source name

..code-block:: python
    api_field = [
            APIField('somename', serializer=ImageRenditionField('fill-300x300').source="myimage")
        ]


Snippets
--------

You can expose your snippet to the API

..code-block:: python

    class SomePage(Page):
        ...
        group = models.ForeignKey('snippet.band', null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

        @property
        def band(self):
            return self.band.name,

        api_fields = [
            APIField('band')


Snippets and streamfield
------------------------

Where streamfields are easy to include in your APIField it takes a littlebit extra work if you use streamfield and
snippets in combination. You have to add the fields to your API manualy in the streamfield block

..code-block:: python

    class BandBlock(blocks.StructBlock):
        band = block.SnippetChooserBlock('snippet.band')

        def get_api_representation(self, value, context=None)
            img = ImageRenditionField('fill-200x200').to_representation(value['band'].image)
            return {'name': value['band'].name,  'image': img}

        class Meta:
            ...

Now these fields will get shown in your API page model if you use the streamfield.
