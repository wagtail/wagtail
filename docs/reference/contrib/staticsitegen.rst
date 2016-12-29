Static site generator
=====================

.. warning::

    django-medusa is no longer maintained, and is incompatible with Django 1.8 and above; the information below is retained for historical reference only. An alternative module based on the `django-bakery`_ package is available as a third-party contribution: https://github.com/mhnbcu/wagtailbakery

This document describes how to render your Wagtail site into static HTML files on your local file system, Amazon S3 or Google App Engine, using `django medusa`_ and the ``wagtail.contrib.wagtailmedusa`` module.

Installing ``django-medusa``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, install ``django-medusa`` and ``django-sendfile`` from pip:

.. code-block:: console

    $ pip install django-medusa django-sendfile

Then add ``django_medusa`` and ``wagtail.contrib.wagtailmedusa`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
       ...
       'django_medusa',
       'wagtail.contrib.wagtailmedusa',
    ]

Define ``MEDUSA_RENDERER_CLASS``, ``MEDUSA_DEPLOY_DIR`` and ``SENDFILE_BACKEND`` in settings:

.. code-block:: python

    MEDUSA_RENDERER_CLASS = 'django_medusa.renderers.DiskStaticSiteRenderer'
    MEDUSA_DEPLOY_DIR = os.path.join(BASE_DIR, 'build')
    SENDFILE_BACKEND = 'sendfile.backends.simple'


Rendering
~~~~~~~~~

To render a site, run ``./manage.py staticsitegen``. This will render the entire website and place the HTML in a folder called ``medusa_output``. The static and media folders need to be copied into this folder manually after the rendering is complete. This feature inherits ``django-medusa``'s ability to render your static site to Amazon S3 or Google App Engine; see the `medusa docs <https://github.com/mtigas/django-medusa/blob/master/README.markdown>`_ for configuration details.

To test, open the ``medusa_output`` folder in a terminal and run ``python -m SimpleHTTPServer`` or ``python3 -m http.server`` respectively.


Advanced topics
~~~~~~~~~~~~~~~

GET parameters
--------------

Pages which require GET parameters (e.g. for pagination) don't generate a suitable file name for the generated HTML files.

Wagtail provides a mixin (``wagtail.contrib.wagtailroutablepage.models.RoutablePageMixin``) which allows you to embed a Django URL configuration into a page. This allows you to give the subpages a URL like ``/page/1/`` which work well with static site generation.


Example:

.. code-block:: python

    from wagtail.contrib.wagtailroutablepage.models import RoutablePageMixin, route


    class BlogIndex(Page, RoutablePageMixin):
        ...

        @route(r'^$', name='main')
        @route(r'^page/(?P<page>\d+)/$', name='page')
        def serve_page(self, request, page=1):
            ...

Then in the template, you can use the ``{% routablepageurl %}`` tag to link between the pages:

.. code-block:: html+django

    {% load wagtailroutablepage_tags %}

    {% if results.has_previous %}
        <a href="{% routablepageurl page 'page' results.previous_page_number %}">Previous page</a>
    {% else %}

    {% if results.has_next %}
        <a href="{% routablepageurl page 'page' results.next_page_number %}">Next page</a>
    {% else %}


Next, you have to tell the ``wagtailmedusa`` module about your custom routing...


Rendering pages which use custom routing
----------------------------------------

For page types that override the ``route`` method, we need to let ``django-medusa`` know which URLs it responds on. This is done by overriding the ``get_static_site_paths`` method to make it yield one string per URL path.

For example, the BlogIndex above would need to yield one URL for each page of results:

.. code-block:: python

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
.. _django-bakery: https://github.com/datadesk/django-bakery
