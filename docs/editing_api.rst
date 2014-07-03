
Defining models with the Editing API
===========

.. note::
    This documentation is currently being written.

Wagtail provides a highly-customizable editing interface consisting of several components:

  * **Fields** — built-in content types to augment the basic types provided by Django
  * **Panels** — the basic editing blocks for fields, groups of fields, and related object clusters
  * **Choosers** — interfaces for finding related objects in a ForeignKey relationship

Configuring your models to use these components will shape the Wagtail editor to your needs. Wagtail also provides an API for injecting custom CSS and JavaScript for further customization, including extending the hallo.js rich text editor.

There is also an Edit Handler API for creating your own Wagtail editor components.

Defining Panels
~~~~~~~~~~~~~~~

A "panel" is the basic editing block in Wagtail. Wagtail will automatically pick the appropriate editing widget for most Django field types; implementors just need to add a panel for each field they want to show in the Wagtail page editor, in the order they want them to appear.

There are four basic types of panels:

  ``FieldPanel( field_name, classname=None )``
    This is the panel used for basic Django field types. ``field_name`` is the name of the class property used in your model definition. ``classname`` is a string of optional CSS classes given to the panel which are used in formatting and scripted interactivity. By default, panels are formatted as inset fields. The CSS class ``full`` can be used to format the panel so it covers the full width of the Wagtail page editor. The CSS class ``title`` can be used to mark a field as the source for auto-generated slug strings.

  ``MultiFieldPanel( children, heading="", classname=None )``
    This panel condenses several ``FieldPanel`` s or choosers, from a list or tuple, under a single ``heading`` string.

  ``InlinePanel( base_model, relation_name, panels=None, classname=None, label='', help_text='' )``
    This panel allows for the creation of a "cluster" of related objects over a join to a separate model, such as a list of related links or slides to an image carousel. This is a very powerful, but tricky feature which will take some space to cover, so we'll skip over it for now. For a full explanation on the usage of ``InlinePanel``, see :ref:`inline_panels`.

  ``FieldRowPanel( children, classname=None)``
    This panel is purely aesthetic. It creates a columnar layout in the editing interface, where each of the child Panels appears alongside each other rather than below. Use of FieldRowPanel particularly helps reduce the "snow-blindness" effect of seeing so many fields on the page, for complex models. It also improves the perceived association between fields of a similar nature. For example if you created a model representing an "Event" which had a starting date and ending date, it may be intuitive to find the start and end date on the same "row".

    FieldRowPanel should be used in combination with ``col*`` classnames added to each of the child Panels of the FieldRowPanel. The Wagtail editing interface is layed out using a grid system, in which the maximum width of the editor is 12 columns wide. Classes ``col1``-``col12`` can be applied to each child of a FieldRowPanel. The class ``col3`` will ensure that field appears 3 columns wide or a quarter the width. ``col4`` would cause the field to be 4 columns wide, or a third the width.

  **(In addition to these four, there are also Chooser Panels, detailed below.)**

Wagtail provides a tabbed interface to help organize panels. Three such tabs are provided:

* ``content_panels`` is the main tab, used for the bulk of your model's fields.
* ``promote_panels`` is suggested for organizing fields regarding the promotion of the page around the site and the Internet. For example, a field to dictate whether the page should show in site-wide menus, descriptive text that should appear in site search results, SEO-friendly titles, OpenGraph meta tag content and other machine-readable information.
* ``settings_panels`` is essentially for non-copy fields. By default it contains the page's scheduled publishing fields. Other suggested fields could include a field to switch between one layout/style and another.

Let's look at an example of a panel definition:

.. code-block:: python

  COMMON_PANELS = (
    FieldPanel('slug'),
    FieldPanel('seo_title'),
    FieldPanel('show_in_menus'),
    FieldPanel('search_description'),
  )

  ...

  class ExamplePage( Page ):
    # field definitions omitted
    ...

  ExamplePage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('body', classname="full"),
    FieldRowPanel([
      FieldPanel('start_date', classname="col3"),
      FieldPanel('end_date', classname="col3"),
    ]),
    ImageChooserPanel('splash_image'),
    DocumentChooserPanel('free_download'),
    PageChooserPanel('related_page'),
  ]

  ExamplePage.promote_panels = [
    MultiFieldPanel(COMMON_PANELS, "Common page configuration"),
  ]

After the ``Page``-derived class definition, just add lists of panel definitions to order and organize the Wagtail page editing interface for your model.


Built-in Fields and Choosers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django's field types are automatically recognized and provided with an appropriate widget for input. Just define that field the normal Django way and pass the field name into ``FieldPanel()`` when defining your panels. Wagtail will take care of the rest.

Here are some Wagtail-specific types that you might include as fields in your models.


Rich Text (HTML)
----------------

Wagtail provides a general-purpose WYSIWYG editor for creating rich text content (HTML) and embedding media such as images, video, and documents. To include this in your models, use the ``RichTextField()`` function when defining a model field:

.. code-block:: python

  from wagtail.wagtailcore.fields import RichTextField
  from wagtail.wagtailadmin.edit_handlers import FieldPanel
  # ...
  class BookPage(Page):
    book_text = RichTextField()

  BookPage.content_panels = [
    FieldPanel('body', classname="full"),
    # ...
  ]

``RichTextField`` inherits from Django's basic ``TextField`` field, so you can pass any field parameters into ``RichTextField`` as if using a normal Django field. This field does not need a special panel and can be defined with ``FieldPanel``.

However, template output from ``RichTextField`` is special and need to be filtered to preserve embedded content. See :ref:`rich-text-filter`.

If you're interested in extending the capabilities of the Wagtail WYSIWYG editor (hallo.js), See :ref:`extending_wysiwyg`.


Images
------

One of the features of Wagtail is a unified image library, which you can access in your models through the ``Image`` model and the ``ImageChooserPanel`` chooser. Here's how:

.. code-block:: python

  from wagtail.wagtailimages.models import Image
  from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
  # ...
  class BookPage(Page):
    cover = models.ForeignKey(
      'wagtailimages.Image',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )

  BookPage.content_panels = [
    ImageChooserPanel('cover'),
    # ...
  ]

Django's default behavior is to "cascade" deletions through a ForeignKey relationship, which is probably not what you want happening. This is why the ``null``, ``blank``, and ``on_delete`` parameters should be set to allow for an empty field. (See `Django model field reference (on_delete)`_ ). ``ImageChooserPanel`` takes only one argument: the name of the field.

.. _Django model field reference (on_delete): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.ForeignKey.on_delete

Displaying ``Image`` objects in a template requires the use of a template tag. See :ref:`image_tag`.


Documents
---------

For files in other formats, Wagtail provides a generic file store through the ``Document`` model:

.. code-block:: python

  from wagtail.wagtaildocs.models import Document
  from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
  # ...
  class BookPage(Page):
    book_file = models.ForeignKey(
      'wagtaildocs.Document',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )

  BookPage.content_panels = [
    DocumentChooserPanel('book_file'),
    # ...
  ]

As with images, Wagtail documents should also have the appropriate extra parameters to prevent cascade deletions across a ForeignKey relationship. ``DocumentChooserPanel`` takes only one argument: the name of the field.

Documents can be used directly in templates without tags or filters. Its properties are:

.. glossary::

  ``title``
    The title of the document.

  ``url``
    URL to the file.

  ``created_at``
    The date and time the document was created (DateTime).

  ``filename``
    The filename of the file.

  ``file_extension``
    The extension of the file.

  ``tags``
    A ``TaggableManager`` which keeps track of tags associated with the document (uses the ``django-taggit`` module).


Pages and Page-derived Models
-----------------------------

You can explicitly link ``Page``-derived models together using the ``Page`` model and ``PageChooserPanel``.

.. code-block:: python

  from wagtail.wagtailcore.models import Page
  from wagtail.wagtailadmin.edit_handlers import PageChooserPanel
  # ...
  class BookPage(Page):
    publisher = models.ForeignKey(
      'wagtailcore.Page',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+',
    )

  BookPage.content_panels = [
    PageChooserPanel('related_page', 'demo.PublisherPage'),
    # ...
  ]

``PageChooserPanel`` takes two arguments: a field name and an optional page type. Specifying a page type (in the form of an ``"appname.modelname"`` string) will filter the chooser to display only pages of that type.


Snippets
--------

Snippets are vanilla Django models you create yourself without a Wagtail-provided base class. So using them as a field in a page requires specifying your own ``appname.modelname``. A chooser, ``SnippetChooserPanel``, is provided which takes the field name and snippet class.

.. code-block:: python

  from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel
  # ...
  class BookPage(Page):
    advert = models.ForeignKey(
      'demo.Advert',
      null=True,
      blank=True,
      on_delete=models.SET_NULL,
      related_name='+'
    )

  BookPage.content_panels = [
    SnippetChooserPanel('advert', Advert),
    # ...
  ]

See :ref:`snippets` for more information.


Field Customization
~~~~~~~~~~~~~~~~~~~

By adding CSS classnames to your panel definitions or adding extra parameters to your field definitions, you can control much of how your fields will display in the Wagtail page editing interface. Wagtail's page editing interface takes much of its behavior from Django's admin, so you may find many options for customization covered there. (See `Django model field reference`_ ).

.. _Django model field reference:https://docs.djangoproject.com/en/dev/ref/models/fields/


Full-Width Input
----------------

Use ``classname="full"`` to make a field (input element) stretch the full width of the Wagtail page editor. This will not work if the field is encapsulated in a ``MultiFieldPanel``, which places its child fields into a formset.


Titles
------

Use ``classname="title"`` to make Page's built-in title field stand out with more vertical padding.


Col*
------

Fields within a ``FieldRowPanel`` can have their width dictated in terms of the number of columns it should span. The ``FieldRowPanel`` is always considered to be 12 columns wide regardless of browser size or the nesting of ``FieldRowPanel`` in any other type of panel. Specify a number of columns thus: ``col3``, ``col4``, ``col6`` etc (up to 12). The resulting width with be *relative* to the full width of the ``FieldRowPanel``.


Required Fields
---------------

To make input or chooser selection manditory for a field, add ``blank=False`` to its model definition. (See `Django model field reference (blank)`_ ).

.. _Django model field reference (blank): https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.blank


Hiding Fields
-------------

Without a panel definition, a default form field (without label) will be used to represent your fields. If you intend to hide a field on the Wagtail page editor, define the field with ``editable=False`` (See `Django model field reference (editable)`_ ).

.. _Django model field reference (editable): https://docs.djangoproject.com/en/dev/ref/models/fields/#editable


MultiFieldPanel
~~~~~~~~~~~~~~~

The ``MultiFieldPanel`` groups a list of child fields into a fieldset, which can also be collapsed into a heading bar to save space.

.. code-block:: python

  BOOK_FIELD_COLLECTION = [
    ImageChooserPanel('cover'),
    DocumentChooserPanel('book_file'),
    PageChooserPanel('publisher'),
  ]

  BookPage.content_panels = [
    MultiFieldPanel(
      BOOK_FIELD_COLLECTION,
      heading="Collection of Book Fields",
      classname="collapsible collapsed"
    ),
    # ...
  ]

By default, ``MultiFieldPanel`` s are expanded and not collapsible. Adding the classname ``collapsible`` will enable the collapse control. Adding both ``collapsible`` and ``collapsed`` to the classname parameter will load the editor page with the ``MultiFieldPanel`` collapsed under its heading.


.. _inline_panels:

Inline Panels and Model Clusters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``django-modelcluster`` module allows for streamlined relation of extra models to a Wagtail page. For instance, you can create objects related through a ``ForeignKey`` relationship on the fly and save them to a draft revision of a ``Page`` object. Normally, your related objects "cluster" would need to be created beforehand (or asynchronously) before linking them to a Page.

Let's look at the example of adding related links to a ``Page``-derived model. We want to be able to add as many as we like, assign an order, and do all of this without leaving the page editing screen.

.. code-block:: python

  from wagtail.wagtailcore.models import Orderable, Page
  from modelcluster.fields import ParentalKey

  # The abstract model for related links, complete with panels
  class RelatedLink(models.Model):
      title = models.CharField(max_length=255)
      link_external = models.URLField("External link", blank=True)

      panels = [
          FieldPanel('title'),
          FieldPanel('link_external'),
      ]

      class Meta:
          abstract = True

  # The real model which combines the abstract model, an
  # Orderable helper class, and what amounts to a ForeignKey link
  # to the model we want to add related links to (BookPage)
  class BookPageRelatedLinks(Orderable, RelatedLink):
      page = ParentalKey('demo.BookPage', related_name='related_links')

  class BookPage( Page ):
    # ...

  BookPage.content_panels = [
    # ...
    InlinePanel( BookPage, 'related_links', label="Related Links" ),
  ]

The ``RelatedLink`` class is a vanilla Django abstract model. The ``BookPageRelatedLinks`` model extends it with capability for being ordered in the Wagtail interface via the ``Orderable`` class as well as adding a ``page`` property which links the model to the ``BookPage`` model we're adding the related links objects to. Finally, in the panel definitions for ``BookPage``, we'll add an ``InlinePanel`` to provide an interface for it all. Let's look again at the parameters that ``InlinePanel`` accepts:

.. code-block:: python

  InlinePanel( base_model, relation_name, panels=None, label='', help_text='' )

``base_model`` is the model you're extending with the cluster. The ``relation_name`` is the ``related_name`` label given to the cluster's ``ParentalKey`` relation. You can add the ``panels`` manually or make them part of the cluster model. Finally, ``label`` and ``help_text`` provide a heading and caption, respectively, for the Wagtail editor.

For another example of using model clusters, see :ref:`tagging`

For more on ``django-modelcluster``, visit `the django-modelcluster github project page`_.

.. _the django-modelcluster github project page: https://github.com/torchbox/django-modelcluster


.. _extending_wysiwyg:

Extending the WYSIWYG Editor (hallo.js)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To inject javascript into the Wagtail page editor, see the :ref:`insert_editor_js` hook. Once you have the hook in place and your hallo.js plugin loads into the Wagtail page editor, use the following Javascript to register the plugin with hallo.js.

.. code-block:: javascript

  registerHalloPlugin(name, opts);

hallo.js plugin names are prefixed with the ``"IKS."`` namespace, but the ``name`` you pass into ``registerHalloPlugin()`` should be without the prefix. ``opts`` is an object passed into the plugin.

For information on developing custom hallo.js plugins, see the project's page: https://github.com/bergie/hallo

Edit Handler API
~~~~~~~~~~~~~~~~

Admin Hooks
-----------

On loading, Wagtail will search for any app with the file ``wagtail_hooks.py`` and execute the contents. This provides a way to register your own functions to execute at certain points in Wagtail's execution, such as when a ``Page`` object is saved or when the main menu is constructed.

Registering functions with a Wagtail hook follows the following pattern:

.. code-block:: python

  from wagtail.wagtailcore import hooks

  hooks.register('hook', function)

Where ``'hook'`` is one of the following hook strings and ``function`` is a function you've defined to handle the hook.

.. _construct_wagtail_edit_bird:

``construct_wagtail_edit_bird``
  Add or remove items from the wagtail userbar. Add, edit, and moderation tools are provided by default. The callable passed into the hook must take the ``request`` object and a list of menu objects, ``items``. The menu item objects must have a ``render`` method which can take a ``request`` object and return the HTML string representing the menu item. See the userbar templates and menu item classes for more information.

  .. code-block:: python

    from wagtail.wagtailcore import hooks

    class UserbarPuppyLinkItem(object):
      def render(self, request):
        return '<li><a href="http://cuteoverload.com/tag/puppehs/" ' \
        + 'target="_parent" class="action icon icon-wagtail">Puppies!</a></li>'

    def add_puppy_link_item(request, items):
      return items.append( UserbarPuppyLinkItem() )

    hooks.register('construct_wagtail_edit_bird', add_puppy_link_item)

.. _construct_homepage_panels:

``construct_homepage_panels``
  Add or remove panels from the Wagtail admin homepage. The callable passed into this hook should take a ``request`` object and a list of ``panels``, objects which have a ``render()`` method returning a string. The objects also have an ``order`` property, an integer used for ordering the panels. The default panels use integers between ``100`` and ``300``.

  .. code-block:: python

    from django.utils.safestring import mark_safe

    from wagtail.wagtailcore import hooks

    class WelcomePanel(object):
      order = 50

      def render(self):
        return mark_safe("""
        <section class="panel summary nice-padding">
          <h3>No, but seriously -- welcome to the admin homepage.</h3>
        </section>
        """)

    def add_another_welcome_panel(request, panels):
      return panels.append( WelcomePanel() )

    hooks.register('construct_homepage_panels', add_another_welcome_panel)

.. _after_create_page:

``after_create_page``
  Do something with a ``Page`` object after it has been saved to the database (as a published page or a revision). The callable passed to this hook should take a ``request`` object and a ``page`` object. The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the Explorer page for the new page's parent.

  .. code-block:: python

    from django.http import HttpResponse

    from wagtail.wagtailcore import hooks

    def do_after_page_create(request, page):
      return HttpResponse("Congrats on making content!", content_type="text/plain")
    hooks.register('after_create_page', do_after_page_create)

.. _after_edit_page:

``after_edit_page``
  Do something with a ``Page`` object after it has been updated. Uses the same behavior as ``after_create_page``.

.. _after_delete_page:

``after_delete_page``
  Do something after a ``Page`` object is deleted. Uses the same behavior as ``after_create_page``.

.. _register_admin_urls:

``register_admin_urls``
  Register additional admin page URLs. The callable fed into this hook should return a list of Django URL patterns which define the structure of the pages and endpoints of your extension to the Wagtail admin. For more about vanilla Django URLconfs and views, see `url dispatcher`_.

  .. _url dispatcher: https://docs.djangoproject.com/en/dev/topics/http/urls/

  .. code-block:: python

    from django.http import HttpResponse
    from django.conf.urls import url

    from wagtail.wagtailcore import hooks

    def admin_view( request ):
      return HttpResponse( \
        "I have approximate knowledge of many things!", \
        content_type="text/plain")

    def urlconf_time():
      return [
        url(r'^how_did_you_almost_know_my_name/$', admin_view, name='frank' ),
      ]
    hooks.register('register_admin_urls', urlconf_time)

.. _construct_main_menu:

``construct_main_menu``
  Add, remove, or alter ``MenuItem`` objects from the Wagtail admin menu. The callable passed to this hook must take a ``request`` object and a list of ``menu_items``; it must return a list of menu items. New items can be constructed from the ``MenuItem`` class by passing in: a ``label`` which will be the text in the menu item, the URL of the admin page you want the menu item to link to (usually by calling ``reverse()`` on the admin view you've set up), CSS class ``name`` applied to the wrapping ``<li>`` of the menu item as ``"menu-{name}"``, CSS ``classnames`` which are used to give the link an icon, and an ``order`` integer which determine's the item's place in the menu.

  .. code-block:: python

    from django.core.urlresolvers import reverse

    from wagtail.wagtailcore import hooks
    from wagtail.wagtailadmin.menu import MenuItem

    def construct_main_menu(request, menu_items):
      menu_items.append(
        MenuItem( 'Frank', reverse('frank'), classnames='icon icon-folder-inverse', order=10000)
      )
    hooks.register('construct_main_menu', construct_main_menu)


.. _insert_editor_js:

``insert_editor_js``
  Add additional Javascript files or code snippets to the page editor. Output must be compatible with ``compress``, as local static includes or string.

  .. code-block:: python

    from django.utils.html import format_html, format_html_join
    from django.conf import settings

    from wagtail.wagtailcore import hooks

    def editor_js():
      js_files = [
        'demo/js/hallo-plugins/hallo-demo-plugin.js',
      ]
      js_includes = format_html_join('\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
      )
      return js_includes + format_html(
        """
        <script>
          registerHalloPlugin('demoeditor');
        </script>
        """
      )
    hooks.register('insert_editor_js', editor_js)

.. _insert_editor_css:

``insert_editor_css``
  Add additional CSS or SCSS files or snippets to the page editor. Output must be compatible with ``compress``, as local static includes or string.

  .. code-block:: python

    from django.utils.html import format_html
    from django.conf import settings

    from wagtail.wagtailcore import hooks

    def editor_css():
      return format_html('<link rel="stylesheet" href="' \
      + settings.STATIC_URL \
      + 'demo/css/vendor/font-awesome/css/font-awesome.min.css">')
    hooks.register('insert_editor_css', editor_css)

.. _construct_whitelister_element_rules:

``construct_whitelister_element_rules``
  .. versionadded:: 0.4
  Customise the rules that define which HTML elements are allowed in rich text areas. By default only a limited set of HTML elements and attributes are whitelisted - all others are stripped out. The callables passed into this hook must return a dict, which maps element names to handler functions that will perform some kind of manipulation of the element. These handler functions receive the element as a `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_ Tag object.

  The ``wagtail.wagtailcore.whitelist`` module provides a few helper functions to assist in defining these handlers: ``allow_without_attributes``, a handler which preserves the element but strips out all of its attributes, and ``attribute_rule`` which accepts a dict specifying how to handle each attribute, and returns a handler function. This dict will map attribute names to either True (indicating that the attribute should be kept), False (indicating that it should be dropped), or a callable (which takes the initial attribute value and returns either a final value for the attribute, or None to drop the attribute).

  For example, the following hook function will add the ``<blockquote>`` element to the whitelist, and allow the ``target`` attribute on ``<a>`` elements:

  .. code-block:: python

    from wagtail.wagtailcore import hooks
    from wagtail.wagtailcore.whitelist import attribute_rule, check_url, allow_without_attributes

    def whitelister_element_rules():
        return {
            'blockquote': allow_without_attributes,
            'a': attribute_rule({'href': check_url, 'target': True}),
        }
    hooks.register('construct_whitelister_element_rules', whitelister_element_rules)


Image Formats in the Rich Text Editor
-------------------------------------

On loading, Wagtail will search for any app with the file ``image_formats.py`` and execute the contents. This provides a way to customize the formatting options shown to the editor when inserting images in the ``RichTextField`` editor.

As an example, add a "thumbnail" format:

.. code-block:: python
  # image_formats.py
  from wagtail.wagtailimages.formats import Format, register_image_format

  register_image_format(Format('thumbnail', 'Thumbnail', 'richtext-image thumbnail', 'max-120x120'))


To begin, import the the ``Format`` class, ``register_image_format`` function, and optionally ``unregister_image_format`` function. To register a new ``Format``, call the ``register_image_format`` with the ``Format`` object as the argument. The ``Format`` takes the following init arguments:

``name``
  The unique key used to identify the format. To unregister this format, call ``unregister_image_format`` with this string as the only argument.

``label``
  The label used in the chooser form when inserting the image into the ``RichTextField``.

``classnames``
  The string to assign to the ``class`` attribute of the generated ``<img>`` tag.

``filter_spec``
  The string specification to create the image rendition. For more, see the :ref:`image_tag`.


To unregister, call ``unregister_image_format`` with the string of the ``name`` of the ``Format`` as the only argument.


Content Index Pages (CRUD)
--------------------------


Custom Choosers
---------------


Tests
-----
