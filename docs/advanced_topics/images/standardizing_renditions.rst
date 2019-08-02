.. _standardizing_renditions:

Standardizing Renditions
========================

The bigger your project gets, the more important it is to keep your rendition
formats organized. So instead of having multiple variations of
rendition-formats sprinkled throughout your code, you try to move them into a
single source of truth, as to not keep repeating yourself.

A practial example, using the popular ``srcset`` attribute for responsive images:

 .. code-block:: html+Django

    {% image box.image width-600 as regular %}
    {% image box.image width-1200 as hidpi_retina %}
    <img src="{{ regular.url }}" srcset="{{ regular.url }} 1x, {{ hidpi_retina.url }} 2x" />

Repeating these filter-specs (``width-600``, ``width-1200``,…) throughout
your project is a tad tedious, a possibility for errors and inconsistencies.
It would be much more convenient to be able to do something along these
lines:

 .. code-block:: html+Django

    {% image box.image filter_specs.medium as regular %}
    {% image box.image filter_specs.large as hidpi_retina %}
    <img src="{{ regular.url }}" srcset="{{ regular.url }} 1x, {{ hidpi_retina.url }} 2x" />

Wagtail lets you do just that, because the filter spec can be a template variable.

You can implement this any way you want. An example is illustrated below.


Setup
-----

We are going to achieve three things:

1. We will unify all filter specs in a common Python file (e.g. ``settings.py``).
2. A context processor will put these specs into our templates.
3. As the filter specs now live in a single place (``settings.py``) you can
   also import them in your Python code.


Common filter specs
^^^^^^^^^^^^^^^^^^^

You can put the filter specs anywhere you want. For most Django projects, this will
be the ``settings.py``, used here as example.

 .. code-block:: python

    # somewhere in your settings.py
    RENDITION_FILTER_SPECS = {
        "thumbnail": "fill-100x100",
        "small": "width-300",
        "medium": "width-600",
        "large": "width-1200",
        "xlarge": "width-1600",
    }

Creating the context processor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now we will make these specs available in the templates, via a context
processor. We assume you add this to ``yourapp/context_processors.py``.

 .. code-block:: python

    # yourapp/context_processors.py
    # Again, assuming you put the RENDITION_FILTER_SPECS in your project's settings.py
    from django.conf import settings


    def filter_specs(request):
        """Exposes our ``RENDITION_FILTER_SPECS`` setting in all templates.

        So we don't have to hardcode image rendition formats throughout all
        of our (template) code.
        """
        return {"filter_specs": settings.RENDITION_FILTER_SPECS}


Installing the context processor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We still have to install our new context processor in the ``settings.py``:

 .. code-block:: python

    TEMPLATES = [
        {
            # ...
            "OPTIONS": {
                "context_processors": [
                    # ...
                    "yourapp.context_processors.filter_specs",
                ]
            },
        }
    ]

Using the filter specs
----------------------

Following are two examples showing how to use these newly standardized filter
specs in your templates and in your Python code.

In the templates
^^^^^^^^^^^^^^^^

 .. code-block:: html+Django

    {% image box.image filter_specs.medium as regular %}
    {% image box.image filter_specs.large as hidpi_retina %}
    <img src="{{ regular.url }}" srcset="{{ regular.url }} 1x, {{ hidpi_retina.url }} 2x" />
    {% image user.avatar filter_specs.thumbnail as avatar %}
    <div class="avatar avatar--small" style="background-image: url('{{ avatar.url }}')"></div>

In your code
^^^^^^^^^^^^

As before, this assumes that you have your filter specs in the ``settings.py``.

 .. code-block:: python

    from django.conf import settings

    # Let's say you want to generate a tiny, low quality, version of an image.
    low_quali_image = myimage.get_rendition(
        "{spec}|jpegquality-25".format(
            spec=settings.RENDITION_FILTER_SPECS['thumbnail']
        )
    )
    # or if you are using Python 3.6 or later and like f-strings
    low_quali_image = myimage.get_rendition(f"{settings.RENDITION_FILTER_SPECS['thumbnail']}|jpegquality-25")
