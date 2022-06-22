(modeladmin_reversing_urls)=

# Reversing ModelAdmin URLs

It's sometimes useful to be able to derive the `index` (listing) or
`create` URLs for a model along with the `edit`, `delete` or
`inspect` URL for a specific object in a model you have registered via
the `modeladmin` app.

Wagtail itself does this by instantiating each `ModelAdmin` class you have
registered, and using the `url_helper` attribute of each instance to
determine what these URLs are.

You can take a similar approach in your own code too, by creating a
`ModelAdmin` instance yourself, and using its `url_helper`
to determine URLs.

See below for some examples:

```{contents}
---
local:
depth: 1
---
```

## Getting the `edit` or `delete` or `inspect` URL for an object

In this example, we will provide a quick way to `edit` the Author that is
linked to a blog post from the admin page listing menu. We have defined
an `AuthorModelAdmin` class and registered it with Wagtail to allow
`Author` objects to be administered via the admin area. The `BlogPage`
model has an `author` field (a `ForeignKey` to the `Author` model)
to allow a single author to be specified for each post.

```python

    # file: wagtail_hooks.py

    from wagtail.admin.widgets import PageListingButton
    from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
    from wagtail import hooks

    # Author & BlogPage model not shown in this example
    from models import Author

    # ensure our modeladmin is created
    class AuthorModelAdmin(ModelAdmin):
        model = Author
        menu_order = 200

    # Creating an instance of `AuthorModelAdmin`
    author_modeladmin = AuthorModelAdmin()

    @hooks.register('register_page_listing_buttons')
    def add_author_edit_buttons(page, page_perms, is_parent=False, next_url=None):
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
```

As you can see from the example above, when using `get_action_url()` to
generate object-specific URLs, the target object's primary key value must be supplied
so that it can be included in the resulting URL (e.g. `"/admin/my-app/author/edit/2/"`).
The following object-specific action names are supported by `get_action_url()`:

-   `'edit'` Returns a URL for updating a specific object.
-   `'delete'` Returns a URL for deleting a specific object.
-   `'inspect'` Returns a URL for viewing details of a specific object.
    -   **NOTE:** This will only work if `inspect_view_enabled` is set to `True` on your `ModelAdmin` class.

```{note}
If you are using string values as primary keys for you model, you may need to handle
cases where the key contains characters that are not URL safe. Only alphanumerics
(`[0-9a-zA-Z]`), or the following special characters are safe:
`$`, `-`, `_`, `.`, `+`, `!`, `*`, `'`, `(`, `)`.

`django.contrib.admin.utils.quote()` can be used to safely encode these primary
key values before passing them to `get_action_url()`. Failure to do this may result
in Wagtail not being able to recognise the primary key when the URL is visited,
resulting in 404 errors.
```

## Getting the `index` or `create` URL for a model

There are URLs available for the model listing view (action is `'index'`) and
the create model view (action is `'create'`). Each of these has an equivalent
shortcut available; `url_helper.index_url` and `url_helper.create_url`.

For example:

```python

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
```

```{note}
If you have registered a page type with `modeladmin` (e.g. `BlogPage`), and pages
of that type can be added to more than one place in the page tree, when a user visits
the `create` URL, they'll be automatically redirected to another view to choose a
parent for the new page. So, this isn't something you need to check or cater for in
your own code.
```

To customise `url_helper` behaviour, see [](modeladmin_url_helper_class).
