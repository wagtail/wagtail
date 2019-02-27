.. _modeladmin_reversing_urls:

=========================
Reversing ModelAdmin URLs
=========================

It's sometimes useful to be able to derive the ``index`` (listing) or
``create`` URLs for a model along with the ``edit``, ``delete`` or
``inspect`` URL for a specific object in a model you have registered via
the ``modeladmin`` app.

Wagtail itself does this by instantiating of each ``ModelAdmin`` class you have
registered, and using the ``url_helper`` attribute of each instance to
determine what these URLs are.

You can take a similar approach in your own code too, by creating a
``ModelAdmin`` instance yourself, and using its ``url_helper``
to determine URLs.

See below for some examples:

.. contents::
    :local:
    :depth: 1

-------------------------------------------------------------------
Getting the ``edit`` or ``delete`` or ``inspect`` URL for an object
-------------------------------------------------------------------

In this example, we will provide a quick way to ``edit`` the Author that is
linked to a blog post from the Admin Page Listing menu. We have defined
an ``AuthorModelAdmin`` class and registered it with Wagtail to allow
``Author`` objects to administered via the admin area. The ``BlogPage`` model
has an ``author`` field (a ``ForeignKey`` to the ``Author`` model) to allow a
single author to be specified for each post.

.. code-block:: python

    # file: wagtail_hooks.py

    from wagtail.admin.widgets import PageListingButton
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from wagtail.core import hooks

    # Authors & BlogPage model not shown in this example
    from models import Authors

    # ensure our modeladmin is created
    class AuthorModelAdmin(ModelAdmin):
        model = Authors
        menu_order = 200

    # Creating an instance of `AuthorModelAdmin`
    author_modeladmin = AuthorModelAdmin()

    @hooks.register('register_page_listing_buttons')
    def page_listing_buttons(page, page_perms, is_parent=False):
        """
        For pages that have an author, add an additional button to the page listing,
        linking to the 'edit' page for that author.
        """
        author_id = getattr(page, 'author_id', None)
        if author_id:
            # the url helper will return something like: /admin/my-app/author/edit/2/
            author_edit_url = author_modeladmin.url_helper.get_action_url('edit', author_id)
            yield PageListingButton('Edit Author',  author_edit_url, priority=10)

    modeladmin_register(AuthorModelAdmin)


In the above example, the ``url_helper`` on the ``AuthorModelAdmin`` class has
been used to generate a URL to edit a ``Author`` instance via ``modeladmin``.

The ``get_action_url`` function should be called with an action name such as
``'edit'`` or ``'delete'`` and with the primary key (ID) of the instance.
This will return a URL to load that action for the specific model in the format
``/admin/my-app/my-page-model/edit/123``.

The action names for a specific instance URLs are:

* ``'edit'``
* ``'delete'``
* ``'inspect'`` Note: Requires inspect enabled in modeladmin configuration.


.. note::
    If your Primary Key for the model is likely to contain characters that
    are not URL safe, ensure you wrap any data in ``quote`` from
    ``django.contrib.admin.utils``.


---------------------------------------------------
Getting the ``index`` or ``create`` URL for a model
---------------------------------------------------

There are URLs available for the model listing view (action is ``'index'``) and
the create model view (action is ``'create'``). Each of these has an equivalent
shortcut available; ``url_helper.index_url`` and ``url_helper.create_url``.

For example:

.. code-block:: python

    from .wagtail_hooks import AuthorModelAdmin

    url_helper = AuthorModelAdmin().url_helper

    index_url = url_helper.get_action_url('index')
    # OR we can use the 'index_url' shortcut
    also_index_url = url_helper.index_url # note: do not call this property as a function
    # both will output /admin/my-app/author

    create_url = url_helper.get_action_url('create')
    # OR we can use the 'create_url' shortcut
    also_create_url = url_helper.create_url # note: do not call this property as a function
    # both will output /admin/my-app/author/create

.. note::

    When creating a new page via ``modeladmin`` it can be created in multiple
    places, there is an additional action ``'choose_parent'`` which is used to
    select the parent **before** creation of a page. There should be no need to
    navigate to this action directly as navigating to the ``create`` URL will
    redirect the user to choose a parent if necessary.

To customise ``url_helper`` behaviour, see :ref:`modeladmin_url_helper_class`.
