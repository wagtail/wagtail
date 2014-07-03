Generating a static site
========================

This document describes how to render your Wagtail site into static HTML files on your local filesystem, Amazon S3 or Google App Engine, using `django medusa`_ and the ``wagtail.contrib.wagtailmedusa`` module.


Installing django-medusa
~~~~~~~~~~~~~~~~~~~~~~~~

First, install django medusa from pip:

.. code::

    pip install django-medusa


Then add ``django_medusa`` and ``wagtail.contrib.wagtailmedusa`` to ``INSTALLED_APPS``:

.. code:: python

    INSTALLED_APPS = [
       ...
       'django_medusa',
       'wagtail.contrib.wagtailmedusa',
    ]


Rendering
~~~~~~~~~

To render a site, run ``./manage.py staticsitegen``. This will render the entire website and place the HTML in a folder called 'medusa_output'. The static and media folders need to be copied into this folder manually after the rendering is complete. This feature inherits django-medusa's ability to render your static site to Amazon S3 or Google App Engine; see the `medusa docs <https://github.com/mtigas/django-medusa/blob/master/README.markdown>`_ for configuration details.

To test, open the 'medusa_output' folder in a terminal and run ``python -m SimpleHTTPServer``.


Advanced topics
~~~~~~~~~~~~~~~

Replacing GET parameters with custom routing
--------------------------------------------

Pages which require GET parameters (e.g. for pagination) don't generate suitable filenames for generated HTML files so they need to be changed to use custom routing instead.

For example, let's say we have a Blog Index which uses pagination. We can override the ``route`` method to make it respond on urls like '/page/1', and pass the page number through to the ``serve`` method:

.. code:: python

    class BlogIndex(Page):
        ...

        def serve(self, request, page=1):
            ...

        def route(self, request, path_components):
            if self.live and len(path_components) == 2 and path_components[0] == 'page':
                try:
                    return self.serve(request, page=int(path_components[1]))
                except (TypeError, ValueError):
                    pass

            return super(BlogIndex, self).route(request, path_components)


Rendering pages which use custom routing
----------------------------------------

For page types that override the ``route`` method, we need to let django medusa know which URLs it responds on. This is done by overriding the ``get_static_site_paths`` method to make it yield one string per URL path.

For example, the BlogIndex above would need to yield one URL for each page of results:

.. code:: python

    def get_static_site_paths(self):
        # Get page count
        page_count = ...

        # Yield a path for each page
        for page in range(page_count):
            yield '/%d/' % (page + 1)

        # Yield from superclass
        for path in super(BlogIndex, self).get_static_site_paths():
            yield path


.. _django medusa: https://github.com/mtigas/django-medusa
