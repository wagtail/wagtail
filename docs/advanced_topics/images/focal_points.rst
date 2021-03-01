Focal points
============

Focal points are used to indicate to Wagtail the area of an image that contains the subject.
This is used by the ``fill`` filter to focus the cropping on the subject, and avoid cropping into it.

Focal points can be defined manually by a Wagtail user, or automatically by using face or feature detection.

Accessing the focal point in templates
--------------------------------------

.. versionadded:: 2.13

You can access the focal point in the template by accessing the ``.focal_point`` attribute of a rendition:

.. code-block:: html+Django

    {% load wagtailimages %}

    {% image myimage width-800 as myrendition %}

    <img
        src="{{ myrendition.url }}"
        alt="{{ myimage.title }}"
        {% if myrendition.focal_point %}
            data-focus-x="{{ myrendition.focal_point.centroid.x }}"
            data-focus-y="{{ myrendition.focal_point.centroid.y }}"
            data-focus-width="{{ myrendition.focal_point.width }}"
            data-focus-height="{{ myrendition.focal_point.height }}"
        {% endif %}
    />
