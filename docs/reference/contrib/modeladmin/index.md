# `ModelAdmin`

The `modeladmin` module allows you to add any model in your project to the Wagtail admin. You can create customisable listing pages for a model, including plain Django models, and add navigation elements so that a model can be accessed directly from the Wagtail admin. Simply extend the `ModelAdmin` class, override a few attributes to suit your needs, register it with Wagtail using an easy one-line `modeladmin_register` method (you can copy and paste from the examples below), and you're good to go. Your model doesn’t need to extend `Page` or be registered as a `Snippet`, and it won’t interfere with any of the existing admin functionality that Wagtail provides.

(modeladmin_feature_summary)=

## Summary of features

-   A customisable list view, allowing you to control what values are displayed for each row, available options for result filtering, default ordering, spreadsheet downloads and more.
-   Access your list views from the Wagtail admin menu easily with automatically generated menu items, with automatic 'active item' highlighting. Control the label text and icons used with easy-to-change attributes on your class.
-   An additional `ModelAdminGroup` class, that allows you to group your related models, and list them together in their own submenu, for a more logical user experience.
-   Simple, robust **add** and **edit** views for your non-Page models that use the panel configurations defined on your model using Wagtail's edit panels.
-   For Page models, the system directs to Wagtail's existing add and edit views, and returns you back to the correct list page, for a seamless experience.
-   Full respect for permissions assigned to your Wagtail users and groups. Users will only be able to do what you want them to!
-   All you need to easily hook your `ModelAdmin` classes into Wagtail, taking care of URL registration, menu changes, and registering any missing model permissions, so that you can assign them to Groups.
-   **Built to be customisable** - While `modeladmin` provides a solid experience out of the box, you can easily use your own templates, and the `ModelAdmin` class has a large number of methods that you can override or extend, allowing you to customise the behaviour to a greater degree.

## Want to know more about customising `ModelAdmin`?

```{toctree}
---
maxdepth: 1
titlesonly:
---
primer
base_url
menu_item
indexview
create_edit_delete_views
inspectview
chooseparentview
tips_and_tricks/index
```

(modeladmin_usage)=

### Installation

Add `wagtail.contrib.modeladmin` to your `INSTALLED_APPS`:

```python
    INSTALLED_APPS = [
       ...
       'wagtail.contrib.modeladmin',
    ]
```

### How to use

(modeladmin_example_simple)=

### A simple example

Let's say your website is for a local library. They have a model called `Book` that appears across the site in many places. You can define a normal Django model for it, then use ModelAdmin to create a menu in Wagtail's admin to create, view, and edit `Book` entries.

`models.py` looks like this:

```python
    from django.db import models
    from wagtail.admin.panels import FieldPanel

    class Book(models.Model):
        title = models.CharField(max_length=255)
        author = models.CharField(max_length=255)
        cover_photo = models.ForeignKey(
            'wagtailimages.Image',
            null=True, blank=True,
            on_delete=models.SET_NULL,
            related_name='+'
        )

        panels = [
            FieldPanel('title'),
            FieldPanel('author'),
            FieldPanel('cover_photo')
        ]
```

```{note}
You can specify panels like `MultiFieldPanel` within the `panels` attribute of the model.
This lets you use Wagtail-specific layouts in an otherwise traditional Django model.
```

`wagtail_hooks.py` in your app directory would look something like this:

```python
    from wagtail.contrib.modeladmin.options import (
        ModelAdmin, modeladmin_register)
    from .models import Book


    class BookAdmin(ModelAdmin):
        model = Book
        base_url_path = 'bookadmin' # customise the URL from default to admin/bookadmin
        menu_label = 'Book'  # ditch this to use verbose_name_plural from model
        menu_icon = 'pilcrow'  # change as required
        menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
        add_to_settings_menu = False  # or True to add your model to the Settings sub-menu
        exclude_from_explorer = False # or True to exclude pages of this type from Wagtail's explorer view
        add_to_admin_menu = True  # or False to exclude your model from the menu
        list_display = ('title', 'author')
        list_filter = ('author',)
        search_fields = ('title', 'author')

    # Now you just need to register your customised ModelAdmin class with Wagtail
    modeladmin_register(BookAdmin)
```

(modeladmin_example_complex)=

### A more complicated example

In addition to `Book`, perhaps we also want to add `Author` and `Genre` models to our app and display a menu item for each of them, too. Creating lots of menus can add up quickly, so it might be a good idea to group related menus together. This section show you how to create one menu called _Library_ which expands to show submenus for _Book_, _Author_, and _Genre_.

Assume we've defined `Book`, `Author`, and `Genre` models in `models.py`.

`wagtail_hooks.py` in your app directory would look something like this:

```python

    from wagtail.contrib.modeladmin.options import (
        ModelAdmin, ModelAdminGroup, modeladmin_register)
    from .models import (
        Book, Author, Genre)


    class BookAdmin(ModelAdmin):
        model = Book
        menu_label = 'Book'  # ditch this to use verbose_name_plural from model
        menu_icon = 'pilcrow'  # change as required
        list_display = ('title', 'author')
        list_filter = ('genre', 'author')
        search_fields = ('title', 'author')


    class AuthorAdmin(ModelAdmin):
        model = Author
        menu_label = 'Author'  # ditch this to use verbose_name_plural from model
        menu_icon = 'user'  # change as required
        list_display = ('first_name', 'last_name')
        list_filter = ('first_name', 'last_name')
        search_fields = ('first_name', 'last_name')


    class GenreAdmin(ModelAdmin):
        model = Genre
        menu_label = 'Genre'  # ditch this to use verbose_name_plural from model
        menu_icon = 'group'  # change as required
        list_display = ('name',)
        list_filter = ('name',)
        search_fields = ('name',)


    class LibraryGroup(ModelAdminGroup):
        menu_label = 'Library'
        menu_icon = 'folder-open-inverse'  # change as required
        menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
        items = (BookAdmin, AuthorAdmin, GenreAdmin)

    # When using a ModelAdminGroup class to group several ModelAdmin classes together,
    # you only need to register the ModelAdminGroup class with Wagtail:
    modeladmin_register(LibraryGroup)
```

(modeladmin_multi_registration)=

### Registering multiple classes in one `wagtail_hooks.py` file

Each time you call `modeladmin_register(MyAdmin)` it creates a new top-level menu item in Wagtail's left sidebar. You can call this multiple times within the same `wagtail_hooks.py` file if you want. The example below will create 3 top-level menus.

```python

    class BookAdmin(ModelAdmin):
        model = Book
        ...

    class MovieAdmin(ModelAdmin):
        model = MovieModel
        ...

    class MusicAdminGroup(ModelAdminGroup):
        menu_label = _("Music")
        items = (AlbumAdmin, ArtistAdmin)
        ...

    modeladmin_register(BookAdmin)
    modeladmin_register(MovieAdmin)
    modeladmin_register(MusicAdminGroup)
```
