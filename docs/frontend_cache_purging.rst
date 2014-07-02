Frontend cache purging
======================

Many websites use a frontend cache such as Varnish, Squid or Cloudflare to gain extra performance. The downside of using a frontend cache though is that they don't respond well to updating content and will often keep an old version of a page cached after it has been updated.

This document describes how to configure Wagtail to purge old versions of pages from a frontend cache whenever a page gets updated.


Setting it up
~~~~~~~~~~~~~

Firstly, add ``"wagtail.contrib.wagtailfrontendcache"`` to your INSTALLED_APPS:

 .. code-block:: python

     INSTALLED_APPS = [
        ...

        "wagtail.contrib.wagtailfrontendcache"
     ]


The ``wagtailfrontendcache`` module provides a set of signal handlers which will automatically purge the cache whenever a page is published or deleted. You should register these somewhere at the top of your ``urls.py`` file:

.. code-block:: python

    # urls.py
    from wagtail.contrib.wagtailfrontendcache.signal_handlers import register_signal_handlers

    register_signal_handlers()


You then need to set the ``WAGTAILFRONTENDCACHE_LOCATION`` setting to the URL of your Varnish/Squid cache server. This must be a direct connection to the server and cannot go through another proxy. By default, this is set to ``http://127.0.0.1:8000`` which is very likely incorrect.

Finally, make sure you have configured your frontend cache to accept PURGE requests:

 - `Varnish <https://www.varnish-cache.org/docs/3.0/tutorial/purging.html>`_
 - `Squid <http://wiki.squid-cache.org/SquidFaq/OperatingSquid#How_can_I_purge_an_object_from_my_cache.3F>`_


Advanced useage
~~~~~~~~~~~~~~~

Purging more than one URL per page
----------------------------------

By default, Wagtail will only purge one URL per page. If your page has more than one URL to be purged, you will need to override the ``get_cached_paths`` method on your page type.

.. code-block:: python

    class BlogIndexPage(Page):
        def get_blog_items(self):
            # This returns a Django paginator of blog items in this section
            return Paginator(self.get_children().live().type(BlogPage), 10)

        def get_cached_paths(self):
            # Yield the main URL
            yield '/'

            # Yield one URL per page in the paginator to make sure all pages are purged
            for page_number in range(1, self.get_blog_items().num_pages):
                yield '/?page=' + str(page_number)


Purging index pages
-------------------

Another problem is pages that list other pages (such as a blog index) will not be purged when a blog entry gets added, changed or deleted. You may want to purge the blog index page so the updates are added into the listing quickly.

This can be solved by using the ``purge_page_from_cache`` utility function which can be found in the ``wagtail.contrib.wagtailfrontendcache.utils`` module.

Let's take the the above BlogIndexPage as an example. We need to register a signal handler to run when one of the BlogPages get updated/deleted. This signal handler should call the ``purge_page_from_cache`` function on all BlogIndexPages that contain the BlogPage being updated/deleted.


.. code-block:: python

    # models.py
    from django.db.models.signals import pre_delete

    from wagtail.wagtailcore.signals import page_published
    from wagtail.contrib.wagtailfrontendcache.utils import purge_page_from_cache


    ...


    def blog_page_changed(blog_page):
        # Find all the live BlogIndexPages that contain this blog_page
        for blog_index in BlogIndexPage.objects.live():
            if blog_page in blog_index.get_blog_items().object_list:
                # Purge this blog index
                purge_page_from_cache(blog_index)


    @register(page_published, sender=BlogPage):
    def blog_published_handler(instance):
        blog_page_changed(instance)


    @register(pre_delete, sender=BlogPage)
    def blog_deleted_handler(instance):
        blog_page_changed(instance)
