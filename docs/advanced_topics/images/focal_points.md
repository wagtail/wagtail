(image_focal_points)=

# Focal points

Focal points are used to indicate to Wagtail the area of an image that contains the subject.
This is used by the `fill` filter to focus the cropping on the subject, and avoid cropping into it.

Focal points can be defined manually by a Wagtail user, or automatically by using face or feature detection.

## Using `focus` attributes on template tags

When using the various image template tags, you can set the `focus` attribute to add information about the image's focal point to the output `<img>` HTML tag. There are a few different values you can supply to control the resulting HTML.

### Using `data-focus-position-*` attributes

By default, the focal point will be set as percentages on two `data-focus-position-{x,y}` attributes on the image. You can also set this behavior explicitly with `focus="data-attr"` on the template tag. For example, the template:

```html+django
{% image page.image width-1024 focus="data-attr" %}
```

Might render HTML like:

```html
<img src="/media/my-image.width-1024.jpg" data-focus-position-x="50%" data-focus-position-y="50%">
```

In newer browsers, you can use the CSS `attr()` function to read these and set `object-position`. For example:

{force=True}
```css
img {
    width: 400px;
    height: 200px;
    object-fit: cover;
    object-position:
        attr(data-focus-position-x type(<length-percentage>), 50%)
        attr(data-focus-position-y type(<length-percentage>), 50%);
}
```

### Using `style` attributes

You can also set `object-position` via a `style` attribute directly on the image by passing `focus="style-attr"` to the template tag. For example, the template:

```html+django
{% image page.image width-1024 focus="style-attr" %}
```

Might render HTML like:

```html
<img src="/media/my-image.width-1024.jpg" style="object-position: 50% 50%;">
```

This is compatible with all major browsers, but the `style` attribute can cause problems if you are using a [content security policy][csp].

### Handling CSP with `<style>` elements

If you are using a [content-security-policy][csp] to protect against XSS attacks involving CSS, you can manually set `object-position` via an inline `<style>` element with a nonce you control:

```html+django
<meta http-equiv="Content-Security-Policy" content="style-src 'nonce-xyz456';">

{% image page.image width-1024 id="my-image" %}
<style type="text/css" nonce="xyz456">
    #my-image {
        {% image page.image original as image_info %}
        object-position:
            {{ image_info.background_position_x }}
            {{ image_info.background_position_y }};
    }
</style>
```

(rendition_background_position_style)=

## Setting the `background-position` inline style based on the focal point

When using a Wagtail image as the background of an element, you can use the `.background_position_style`
attribute on the rendition to position the rendition based on the focal point in the image:

```html+django
{% image page.image width-1024 as image %}

<div style="background-image: url('{{ image.url }}'); {{ image.background_position_style }}">
</div>
```

For sites enforcing a Content Security Policy, you can apply those styles via a `<style>` tag with a `nonce` attribute.

## Accessing the focal point in templates

You can access the focal point in the template by accessing the `.focal_point` attribute of a rendition:

```html+django
{% load wagtailimages_tags %}

{% image page.image width-800 as myrendition %}

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


[csp]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP
