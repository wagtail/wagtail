(using_images_outside_wagtail)=

# Dynamic image serve view

In most cases, developers wanting to generate image renditions in Python should use the `get_rendition()`
method. See [](image_renditions).

If you need to be able to generate image versions for an _external_ system such as a blog or mobile app,
Wagtail provides a view for dynamically generating renditions of images by calling a unique URL.

The view takes an image id, filter spec and security signature in the URL. If
these parameters are valid, it serves an image file matching that criteria.

Like the `{% image %}` tag, the rendition is generated on the first call and
subsequent calls are served from a cache.

## Setup

Add an entry for the view into your URLs configuration:

```python
from wagtail.images.views.serve import ServeView

urlpatterns = [
    ...

    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(), name='wagtailimages_serve'),

    ...

    # Ensure that the wagtailimages_serve line appears above the default Wagtail page serving route
    re_path(r'', include(wagtail_urls)),
]
```

## Usage

### Image URL generator UI

When the dynamic serve view is enabled, an image URL generator in the admin
interface becomes available automatically. This can be accessed through the edit
page of any image by clicking the "URL generator" button on the right hand side.

This interface allows editors to generate URLs to cropped versions of the image.

### Generating dynamic image URLs in Python

Dynamic image URLs can also be generated using Python code and served to a
client over an API or used directly in the template.

One advantage of using dynamic image URLs in the template is that they do not
block the initial response while rendering like the `{% image %}` tag does.

The `generate_image_url` function in `wagtail.images.views.serve` is a convenience
method to generate a dynamic image URL.

Here's an example of this being used in a view:

```python
def display_image(request, image_id):
    image = get_object_or_404(Image, id=image_id)

    return render(request, 'display_image.html', {
        'image_url': generate_image_url(image, 'fill-100x100')
    })
```

Image operations can be chained by joining them with a `|` character:

```python
return render(request, 'display_image.html', {
    'image_url': generate_image_url(image, 'fill-100x100|jpegquality-40')
})
```

In your templates:

```html+django
{% load wagtailimages_tags %}
...

<!-- Get the url for the image scaled to a width of 400 pixels: -->
{% image_url page.photo "width-400" %}

<!-- Again, but this time as a square thumbnail: -->
{% image_url page.photo "fill-100x100|jpegquality-40" %}

<!-- This time using our custom image serve view: -->
{% image_url page.photo "width-400" "mycustomview_serve" %}
```

You can pass an optional view name that will be used to serve the image through. The default is `wagtailimages_serve`

## Advanced configuration

(image_serve_view_redirect_action)=

### Making the view redirect instead of serve

By default, the view will serve the image file directly. This behaviour can be
changed to a 301 redirect instead which may be useful if you host your images
externally.

To enable this, pass `action='redirect'` into the `ServeView.as_view()`
method in your urls configuration:

```python
from wagtail.images.views.serve import ServeView

urlpatterns = [
    ...

    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(action='redirect'), name='wagtailimages_serve'),
]
```

(image_serve_view_sendfile)=

## Integration with django-sendfile

[django-sendfile](https://github.com/johnsensible/django-sendfile) offloads the job of transferring the image data to the web
server instead of serving it directly from the Django application. This could
greatly reduce server load in situations where your site has many images being
downloaded but you're unable to use a [](caching_proxy) or a CDN.

You firstly need to install and configure django-sendfile and configure your
web server to use it. If you haven't done this already, please refer to the
[installation docs](https://github.com/johnsensible/django-sendfile#django-sendfile).

To serve images with django-sendfile, you can use the `SendFileView` class.
This view can be used out of the box:

```python
from wagtail.images.views.serve import SendFileView

urlpatterns = [
    ...

    re_path(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', SendFileView.as_view(), name='wagtailimages_serve'),
]
```

You can customise it to override the backend defined in the `SENDFILE_BACKEND`
setting:

```python
from wagtail.images.views.serve import SendFileView
from project.sendfile_backends import MyCustomBackend

class MySendFileView(SendFileView):
    backend = MyCustomBackend
```

You can also customise it to serve private files. For example, if the only need
is to be authenticated (e.g. for Django >= 1.9):

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from wagtail.images.views.serve import SendFileView

class PrivateSendFileView(LoginRequiredMixin, SendFileView):
    raise_exception = True
```
