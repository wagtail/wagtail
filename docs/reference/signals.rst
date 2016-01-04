.. _signals:

Signals
=======

Wagtail's `PageRevision <./pages/model_reference#pagerevision>`__  and
`Page <./pages/model_reference#page>`__  implement
`Signals <https://docs.djangoproject.com/en/1.8/topics/signals/>`__ from ``django.dispatch``.
Signals are useful for creating side-effects from page publish/unpublish events.

Primarily, these are used by the `Frontend Cache <./contrib/frontendcache>`__ contrib module
and the `Wagtail API <./contrib/api/index>`__. You could also use signals to send
publish notifications to a messaging service, or ``POST`` messages to another
app that's consuming the API, such as a static site generator.


page_published
--------------

This signal is emitted from a ``PageRevision`` when a revision is set to `published`.

:sender: The page ``class``
:instance: The specific ``Page`` instance.
:revision: The ``PageRevision`` that was published
:kwargs: Any other arguments passed to ``page_published.send()``.

To listen to a signal, implement ``page_published.connect(receiver, sender, **kwargs)``. Here's a simple
example showing how you might notify your team when something is published:

.. code-block:: python

    from wagtail.wagtailcore.signals import page_published
    import urllib
    import urllib2


    # Let everyone know when a new page is published
    def send_to_slack(sender, **kwargs):
        instance = kwargs['instance']
        url = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
        values = {
            "text" : "%s was published by %s " % (instance.title, instance.owner.username),
            "channel": "#publish-notifications",
            "username": "the squid of content",
            "icon_emoji": ":octopus:"
        }

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)

    # Register a receiver
    page_published.connect(send_to_slack)


Receiving specific model events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you're not interested in receiving signals for every model, or you want
to handle signals for specific models in different ways. For instance, you may
wish to do something when a new blog post is published:

.. code-block:: python

    from wagtail.wagtailcore.signals import page_published
    from mysite.models import BlogPostPage

    # Do something clever for each model type
    def receiver(model, **kwargs):
        # Do something with blog posts
        pass

    # Register listeners for each page model class
    page_published.connect(receiver, sender=BlogPostPage)

Wagtail provides access to a list of registered page types through the ``get_page_models()`` function in ``wagtail.wagtailcore.models``.

Read the `Django documentation <https://docs.djangoproject.com/en/1.8/topics/signals/#connecting-to-specific-signals>`__ for more information about specifying senders.


page_unpublished
----------------

This signal is emitted from a ``Page`` when the page is unpublished.

:sender: The page ``class``
:instance: The specific ``Page`` instance.
:kwargs: Any other arguments passed to ``page_unpublished.send()``
