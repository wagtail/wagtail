.. _using_images_outside_wagtail:

========================
Dynamic image serve view
========================

Wagtail provides a view for dynamically generating renditions of images. It can
be called by an external system (eg a blog or mobile app) or used internally as
an alternative to Wagtail's ``{% image %}`` tag.

The view takes an image id, filter spec and security signature in the URL. If
these parameters are valid, it serves an image file matching that criteria.

Like the ``{% image %}`` tag, the rendition is generated on the first call and
subsequent calls are served from a cache.

Setup
=====

Add an entry for the view into your URLs configuration:

 .. code-block:: python

    from wagtail.wagtailimages.views.serve import ServeView

    urlpatterns = [
        ...

        url(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(), name='wagtailimages_serve'),

        ...

        # Ensure that the wagtailimages_serve line appears above the default Wagtail page serving route
        url(r'', include(wagtail_urls)),
    ]

Usage
=====

Image URL generator UI
----------------------

When the dynamic serve view is enabled, an image URL generator in the admin
interface becomes available automatically. This can be accessed through the edit
page of any image by clicking the "URL generator" button on the right hand side.

This interface allows editors to generate URLs to cropped versions of the image.

Generating dynamic image URLs in Python
---------------------------------------

Dynamic image URLs can also be generated using Python code and served to a
client over an API or used directly in the template.

One advantage of using dynamic image URLs in the template is that they do not
block the initial response while rendering like the ``{% image %}`` tag does.

.. code-block:: python

    from django.core.urlresolvers import reverse
    from wagtail.wagtailimages.views.serve import generate_signature

    def generate_image_url(image, filter_spec):
        signature = generate_signature(image.id, filter_spec)
        url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))

        # Append image's original filename to the URL (optional)
        url += image.file.name[len('original_images/'):]

        return url

And here's an example of this being used in a view:

.. code-block:: python

    def display_image(request, image_id):
        image = get_object_or_404(Image, id=image_id)

        return render(request, 'display_image.html', {
            'image_url': generate_image_url(image, 'fill-100x100')
        })


Image operations can be chained by joining them with a ``|`` character:

.. code-block:: python

        return render(request, 'display_image.html', {
            'image_url': generate_image_url(image, 'fill-100x100|jpegquality-40')
        })


Advanced configuration
======================

.. _image_serve_view_redirect_action:

Making the view redirect instead of serve
-----------------------------------------

By default, the view will serve the image file directly. This behaviour can be
changed to a 301 redirect instead which may be useful if you host your images
externally.

To enable this, pass ``action='redirect'`` into the ``ServeView.as_view()``
method in your urls configuration:

.. code-block:: python

   from wagtail.wagtailimages.views.serve import ServeView

   urlpatterns = [
       ...

       url(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', ServeView.as_view(action='redirect'), name='wagtailimages_serve'),
   ]

.. _image_serve_view_sendfile:

Integration with django-sendfile
--------------------------------

`django-sendfile`_ offloads the job of transferring the image data to the web
server instead of serving it directly from the Django application. This could
greatly reduce server load in situations where your site has many images being
downloaded but you're unable to use a :ref:`caching_proxy` or a CDN.

.. _django-sendfile: https://github.com/johnsensible/django-sendfile

You firstly need to install and configure django-sendfile and configure your
web server to use it. If you haven't done this already, please refer to the
`installation docs <https://github.com/johnsensible/django-sendfile#django-sendfile>`_.

To serve images with django-sendfile, you can use the ``SendFileView`` class.
This view can be used out of the box:

.. code-block:: python

   from wagtail.wagtailimages.views.serve import SendFileView

   urlpatterns = [
       ...

       url(r'^images/([^/]*)/(\d*)/([^/]*)/[^/]*$', SendFileView.as_view(), name='wagtailimages_serve'),
   ]

You can customise it to override the backend defined in the ``SENDFILE_BACKEND``
setting:

.. code-block:: python

    from wagtail.wagtailimages.views.serve import SendFileView
    from project.sendfile_backends import MyCustomBackend

    class MySendFileView(SendFileView):
        backend = MyCustomBackend

You can also customise it to serve private files. For example, if the only need
is to be authenticated (e.g. for Django >= 1.9):

.. code-block:: python

    from django.contrib.auth.mixins import LoginRequiredMixin
    from wagtail.wagtailimages.views.serve import SendFileView

    class PrivateSendFileView(LoginRequiredMixin, SendFileView):
        raise_exception = True
