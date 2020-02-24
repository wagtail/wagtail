.. _signals:

Signals
=======

Wagtail's :ref:`page-revision-model-ref` and :ref:`page-model-ref` implement
:doc:`Signals <topics/signals>` from ``django.dispatch``.
Signals are useful for creating side-effects from page publish/unpublish events.

For example, you could use signals to send publish notifications to a messaging service, or ``POST`` messages to another app that's consuming the API, such as a static site generator.


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

    from wagtail.core.signals import page_published
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

    from wagtail.core.signals import page_published
    from mysite.models import BlogPostPage

    # Do something clever for each model type
    def receiver(sender, **kwargs):
        # Do something with blog posts
        pass

    # Register listeners for each page model class
    page_published.connect(receiver, sender=BlogPostPage)

Wagtail provides access to a list of registered page types through the ``get_page_models()`` function in ``wagtail.core.models``.

Read the :ref:`Django documentation <connecting-to-specific-signals>` for more information about specifying senders.


page_unpublished
----------------

This signal is emitted from a ``Page`` when the page is unpublished.

:sender: The page ``class``
:instance: The specific ``Page`` instance.
:kwargs: Any other arguments passed to ``page_unpublished.send()``


workflow_submitted
------------------

This signal is emitted from a ``WorkflowState`` when a page is submitted to a workflow.

:sender: ``WorkflowState``
:instance: The specific ``WorkflowState`` instance.
:user: The user who submitted the workflow
:kwargs: Any other arguments passed to ``workflow_submitted.send()``


workflow_rejected
-----------------

This signal is emitted from a ``WorkflowState`` when a page is rejected from a workflow.

:sender: ``WorkflowState``
:instance: The specific ``WorkflowState`` instance.
:user: The user who rejected the workflow
:kwargs: Any other arguments passed to ``workflow_rejected.send()``


workflow_approved
-----------------

This signal is emitted from a ``WorkflowState`` when a page's workflow completes successfully

:sender: ``WorkflowState``
:instance: The specific ``WorkflowState`` instance.
:user: The user who last approved the workflow
:kwargs: Any other arguments passed to ``workflow_approved.send()``


workflow_cancelled
------------------

This signal is emitted from a ``WorkflowState`` when a page's workflow is cancelled

:sender: ``WorkflowState``
:instance: The specific ``WorkflowState`` instance.
:user: The user who cancelled the workflow
:kwargs: Any other arguments passed to ``workflow_cancelled.send()``


task_submitted
--------------

This signal is emitted from a ``TaskState`` when a page is submitted to a task.

:sender: ``TaskState``
:instance: The specific ``TaskState`` instance.
:user: The user who submitted the page to the task
:kwargs: Any other arguments passed to ``task_submitted.send()``


task_rejected
-------------

This signal is emitted from a ``TaskState`` when a page is rejected from a task.

:sender: ``TaskState``
:instance: The specific ``TaskState`` instance.
:user: The user who rejected the task
:kwargs: Any other arguments passed to ``task_rejected.send()``


task_approved
-------------

This signal is emitted from a ``TaskState`` when a page's task is approved

:sender: ``TaskState``
:instance: The specific ``TaskState`` instance.
:user: The user who approved the task
:kwargs: Any other arguments passed to ``task_approved.send()``


task_cancelled
--------------

This signal is emitted from a ``TaskState`` when a page's task is cancelled.

:sender: ``TaskState``
:instance: The specific ``TaskState`` instance.
:user: The user who cancelled the task
:kwargs: Any other arguments passed to ``task_cancelled.send()``