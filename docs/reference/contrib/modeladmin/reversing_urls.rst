.. _modeladmin_reversing_urls:

=========================
Reversing ModelAdmin URLs
=========================

``modeladmin`` provides a convenient set of ``url_helper`` methods to get
admin URLs for the various views such as ``create``, ``delete``, ``inpsect``
or ``edit``, along with a model listing via ``index``.

.. contents::
    :local:
    :depth: 1

-------------------------------------------
Getting the URL for Edit, Delete or Inspect
-------------------------------------------

In this example, our goal is to provide a quick way to ``edit`` the Author
that is linked to a blog post from the Admin Page Listing menu. Where we
have a ``modeladmin`` called ``AuthorModelAdmin`` which uses the model
``Authors`` and our ``BlogPage`` model has a foreign key to a single Author.

.. code-block:: python

    # file: wagtail_hooks.py

    from wagtail.admin import widgets as wagtailadmin_widgets
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from wagtail.core import hooks

    # Authors & BlogPage model not shown in this example
    from models import Authors

    # ensure our modeladmin is created
    class AuthorModelAdmin(ModelAdmin):
        model = Authors
        menu_order = 200

    # use the url_helper to create a button on the page listing if author present
    @hooks.register('register_page_listing_buttons')
    def page_listing_buttons(page, page_perms, is_parent=False):
        page_author = getattr(page, 'page_author', False)
        # only yield a button if we know an author is linked
        if page_author:
            url_helper = AuthorModelAdmin().url_helper # initialise modeladmin
            edit_author_url = url_helper.get_action_url('edit', page_author.pk)
            # edit_page_author_url will output /admin/my-app/author/edit/2/
            yield wagtailadmin_widgets.PageListingButton(
                'Edit Author',
                edit_author_url,
                priority=10
            )

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
* ``'inspect'`` **requires inspect enabled in modeladmin configuration**


.. note::
    If your Primary Key for the model is likely to contain characters that
    are not URL safe, ensure you wrap any data in ``quote`` from
    ``django.contrib.admin.utils``.


----------------------------------
Getting the URL for Create & Index
----------------------------------

There are URLs available for the model listing view and the create model view,
these have the action names ``'index'`` and ``'create'``.

Both of these URLs are also available via the ``url_helper`` as cached
properties; ``url_helper.index_url`` and ``url_helper.create_url``.

For example:

.. code-block:: python

    from .wagtail_hooks import AuthorModelAdmin

    url_helper = AuthorModelAdmin().url_helper

    index_url = url_helper.get_action_url('index')
    # OR we can use the cached property which is easier
    also_index_url = url_helper.index_url # remember do not call this property as a function
    # will output /admin/my-app/author

    create_url = url_helper.get_action_url('create')
    # OR we can use the cached property which is easier
    also_create_url = url_helper.create_url # remember do not call this property as a function
    # will output /admin/my-app/author/create

.. note::

    When creating a new page via ``modeladmin`` it can be created in multiple
    places, there is an additional action ``'choose_parent'`` which is used to
    select the parent **before** creation of a page. There should be no need to
    navigate to this action directly as navigating to the ``create`` URL will
    redirect the user to choose a parent if necessary.

To customise ``url_helper`` behaviour, see :ref:`modeladmin_url_helper_class`.
