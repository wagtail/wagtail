.. _signals:

==================
How to use Signals
==================

Wagtail's :ref:`page-revision-model-ref` and :ref:`page-model-ref` implement
:doc:`Signals <topics/signals>` from ``django.dispatch``.
Signals are useful for creating side-effects from page publish/unpublish events.

***************
Example for using signals
***************

To use signals you need to create/modify three files inside your app:

1. singals.py
2. apps.py
3. __init__.py

Here is a short example that prints "Hello world!" when a page is published.

We have:

- App named: ``blog``
- Model named: ``BlogPage``

We configure the files 

`singals.py`:
===============

.. code-block:: python

    from wagtail.core.signals import page_published
    from blog.models import BlogPage
    
    # Do something clever for each model type
    def receiver(sender, **kwargs):
        # Do something with blog posts
        print("Hello world!")
    
    # Register listeners for each page model class
    page_published.connect(receiver, sender=BlogPage)
    


`apps.py`:
===============

.. code-block:: python

    from django.apps import AppConfig
    
    
    class BlogConfig(AppConfig):
        name = 'blog'
    
        def ready(self):
            import blog.signals  # noqa
    
`__init__.py`:
===============

.. code-block:: python

    default_app_config = 'blog.apps.BlogConfig'


Now whenever a page is published the signal will be sent. for more information about signals check `Singals reference <https://docs.wagtail.io/en/stable/reference/signals.html>`_
