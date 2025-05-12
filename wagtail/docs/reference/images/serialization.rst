Image serialization
===================

Wagtail now provides a `ModelSerializer` for the `Image` model using Django REST Framework.

Serializer
----------

The `ImageSerializer` enables serialization of `Image` model instances including all fields:

.. code-block:: python

    from wagtail.images.serializers import ImageSerializer

    serializer = ImageSerializer(instance=image)
    print(serializer.data)

Natural key
-----------

The `ImageSerializer` also provides a `natural_key` static method:

.. code-block:: python

    ImageSerializer.natural_key(image)

This returns the file name (path) of the image:

.. code-block:: text

    "images/example.jpg"

This can be used for more deterministic fixture generation or serialization where object identity needs to be preserved across environments.
