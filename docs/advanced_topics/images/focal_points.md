# Focal points

Focal points are used to indicate to Wagtail the area of an image that contains the subject.
This is used by the `fill` filter to focus the cropping on the subject, and avoid cropping into it.

Focal points can be defined manually by a Wagtail user, or automatically by using face or feature detection.

(rendition_background_position_style)=

## Setting the `background-position` inline style based on the focal point

When using a Wagtail image as the background of an element, you can use the `.background_position_style`
attribute on the rendition to position the rendition based on the focal point in the image:

```html+django
{% image page.image width-1024 as image %}

<div style="background-image: url('{{ image.url }}'); {{ image.background_position_style }}">
</div>
```

## Accessing the focal point in templates

You can access the focal point in the template by accessing the `.focal_point` attribute of a rendition:

```html+django
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
```
