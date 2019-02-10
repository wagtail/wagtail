
.. _admin_hooks:

Hooks
=====

On loading, Wagtail will search for any app with the file ``wagtail_hooks.py`` and execute the contents. This provides a way to register your own functions to execute at certain points in Wagtail's execution, such as when a ``Page`` object is saved or when the main menu is constructed.

Registering functions with a Wagtail hook is done through the ``@hooks.register`` decorator:

.. code-block:: python

  from wagtail.core import hooks

  @hooks.register('name_of_hook')
  def my_hook_function(arg1, arg2...)
      # your code here


Alternatively, ``hooks.register`` can be called as an ordinary function, passing in the name of the hook and a handler function defined elsewhere:

.. code-block:: python

  hooks.register('name_of_hook', my_hook_function)

If you need your hooks to run in a particular order, you can pass the ``order`` parameter:

.. code-block:: python

  @hooks.register('name_of_hook', order=1)  # This will run after every hook in the wagtail core
  def my_hook_function(arg1, arg2...)
      # your code here

  @hooks.register('name_of_hook', order=-1)  # This will run before every hook in the wagtail core
  def my_other_hook_function(arg1, arg2...)
      # your code here

  @hooks.register('name_of_hook', order=2)  # This will run after `my_hook_function`
  def yet_another_hook_function(arg1, arg2...)
      # your code here

The available hooks are listed below.

.. contents::
    :local:
    :depth: 1


Admin modules
-------------

Hooks for building new areas of the admin interface (alongside pages, images, documents and so on).

.. _construct_homepage_panels:

``construct_homepage_panels``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add or remove panels from the Wagtail admin homepage. The callable passed into this hook should take a ``request`` object and a list of ``panels``, objects which have a ``render()`` method returning a string. The objects also have an ``order`` property, an integer used for ordering the panels. The default panels use integers between ``100`` and ``300``.

  .. code-block:: python

    from django.utils.safestring import mark_safe

    from wagtail.core import hooks

    class WelcomePanel:
        order = 50

        def render(self):
            return mark_safe("""
            <section class="panel summary nice-padding">
              <h3>No, but seriously -- welcome to the admin homepage.</h3>
            </section>
            """)

    @hooks.register('construct_homepage_panels')
    def add_another_welcome_panel(request, panels):
      return panels.append( WelcomePanel() )


.. _construct_homepage_summary_items:

``construct_homepage_summary_items``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add or remove items from the 'site summary' bar on the admin homepage (which shows the number of pages and other object that exist on the site). The callable passed into this hook should take a ``request`` object and a list of ``SummaryItem`` objects to be modified as required. These objects have a ``render()`` method, which returns an HTML string, and an ``order`` property, which is an integer that specifies the order in which the items will appear.


.. _construct_main_menu:

``construct_main_menu``
~~~~~~~~~~~~~~~~~~~~~~~

  Called just before the Wagtail admin menu is output, to allow the list of menu items to be modified. The callable passed to this hook will receive a ``request`` object and a list of ``menu_items``, and should modify ``menu_items`` in-place as required. Adding menu items should generally be done through the ``register_admin_menu_item`` hook instead - items added through ``construct_main_menu`` will be missing any associated JavaScript includes, and their ``is_shown`` check will not be applied.

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('construct_main_menu')
    def hide_explorer_menu_item_from_frank(request, menu_items):
      if request.user.username == 'frank':
        menu_items[:] = [item for item in menu_items if item.name != 'explorer']


.. _describe_collection_contents:

``describe_collection_contents``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when Wagtail needs to find out what objects exist in a collection, if any. Currently this happens on the confirmation before deleting a collection, to ensure that non-empty collections cannot be deleted. The callable passed to this hook will receive a ``collection`` object, and should return either ``None`` (to indicate no objects in this collection), or a dict containing the following keys:

``count``
  A numeric count of items in this collection

``count_text``
  A human-readable string describing the number of items in this collection, such as "3 documents". (Sites with multi-language support should return a translatable string here, most likely using the ``django.utils.translation.ungettext`` function.)

``url`` (optional)
  A URL to an index page that lists the objects being described.

.. _register_account_menu_item:

``register_account_menu_item``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add an item to the “Account settings” page within the Wagtail admin.
  The callable for this hook should return a dict with the keys
  ``url``, ``label`` and ``help_text``. For example:

  .. code-block:: python

    from django.urls import reverse
    from wagtail.core import hooks

    @hooks.register('register_account_menu_item')
    def register_account_delete_account(request):
        return {
            'url': reverse('delete-account'),
            'label': 'Delete account',
            'help_text': 'This permanently deletes your account.'
        }



.. _register_admin_menu_item:

``register_admin_menu_item``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add an item to the Wagtail admin menu. The callable passed to this hook must return an instance of ``wagtail.admin.menu.MenuItem``. New items can be constructed from the ``MenuItem`` class by passing in a ``label`` which will be the text in the menu item, and the URL of the admin page you want the menu item to link to (usually by calling ``reverse()`` on the admin view you've set up). Additionally, the following keyword arguments are accepted:

  :name: an internal name used to identify the menu item; defaults to the slugified form of the label.
  :classnames: additional classnames applied to the link, used to give it an icon
  :attrs: additional HTML attributes to apply to the link
  :order: an integer which determines the item's position in the menu

  ``MenuItem`` can be subclassed to customise the HTML output, specify JavaScript files required by the menu item, or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (``wagtail/wagtailadmin/menu.py``) for details.

  .. code-block:: python

    from django.urls import reverse

    from wagtail.core import hooks
    from wagtail.admin.menu import MenuItem

    @hooks.register('register_admin_menu_item')
    def register_frank_menu_item():
      return MenuItem('Frank', reverse('frank'), classnames='icon icon-folder-inverse', order=10000)


.. _register_admin_urls:

``register_admin_urls``
~~~~~~~~~~~~~~~~~~~~~~~

  Register additional admin page URLs. The callable fed into this hook should return a list of Django URL patterns which define the structure of the pages and endpoints of your extension to the Wagtail admin. For more about vanilla Django URLconfs and views, see :doc:`url dispatcher <django:topics/http/urls>`.

  .. code-block:: python

    from django.http import HttpResponse
    from django.conf.urls import url

    from wagtail.core import hooks

    def admin_view(request):
      return HttpResponse(
        "I have approximate knowledge of many things!",
        content_type="text/plain")

    @hooks.register('register_admin_urls')
    def urlconf_time():
      return [
        url(r'^how_did_you_almost_know_my_name/$', admin_view, name='frank'),
      ]


.. _register_group_permission_panel:

``register_group_permission_panel``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add a new panel to the Groups form in the 'settings' area. The callable passed to this hook must return a ModelForm / ModelFormSet-like class, with a constructor that accepts a group object as its ``instance`` keyword argument, and which implements the methods ``save``, ``is_valid``, and ``as_admin_panel`` (which returns the HTML to be included on the group edit page).


.. _register_settings_menu_item:

``register_settings_menu_item``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  As ``register_admin_menu_item``, but registers menu items into the 'Settings' sub-menu rather than the top-level menu.


.. _register_admin_search_area:

``register_admin_search_area``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add an item to the Wagtail admin search "Other Searches". Behaviour of this hook is similar to ``register_admin_menu_item``. The callable passed to this hook must return an instance of ``wagtail.admin.search.SearchArea``. New items can be constructed from the ``SearchArea`` class by passing the following parameters:

  :label: text displayed in the "Other Searches" option box.
  :name: an internal name used to identify the search option; defaults to the slugified form of the label.
  :url: the URL of the target search page.
  :classnames: additional CSS classnames applied to the link, used to give it an icon.
  :attrs: additional HTML attributes to apply to the link.
  :order: an integer which determines the item's position in the list of options.

  Setting the URL can be achieved using reverse() on the target search page. The GET parameter 'q' will be appended to the given URL.

  A template tag, ``search_other`` is provided by the ``wagtailadmin_tags`` template module. This tag takes a single, optional parameter, ``current``, which allows you to specify the ``name`` of the search option currently active. If the parameter is not given, the hook defaults to a reverse lookup of the page's URL for comparison against the ``url`` parameter.


  ``SearchArea`` can be subclassed to customise the HTML output, specify JavaScript files required by the option, or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (``wagtail/wagtailadmin/search.py``) for details.

  .. code-block:: python

    from django.urls import reverse
    from wagtail.core import hooks
    from wagtail.admin.search import SearchArea

    @hooks.register('register_admin_search_area')
    def register_frank_search_area():
        return SearchArea('Frank', reverse('frank'), classnames='icon icon-folder-inverse', order=10000)


.. _register_permissions:

``register_permissions``
~~~~~~~~~~~~~~~~~~~~~~~~

  Return a QuerySet of ``Permission`` objects to be shown in the Groups administration area.


.. _filter_form_submissions_for_user:

``filter_form_submissions_for_user``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Allows access to form submissions to be customised on a per-user, per-form basis.

  This hook takes two parameters:
   - The user attempting to access form submissions
   - A ``QuerySet`` of form pages

  The hook must return a ``QuerySet`` containing a subset of these form pages which the user is allowed to access the submissions for.

  For example, to prevent non-superusers from accessing form submissions:

  .. code-block:: python

    from wagtail.core import hooks


    @hooks.register('filter_form_submissions_for_user')
    def construct_forms_for_user(user, queryset):
        if not user.is_superuser:
            queryset = queryset.none()

        return queryset



Editor interface
----------------

Hooks for customising the editing interface for pages and snippets.


.. _register_rich_text_features:

``register_rich_text_features``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Rich text fields in Wagtail work with a list of 'feature' identifiers that determine which editing controls are available in the editor, and which elements are allowed in the output; for example, a rich text field defined as ``RichTextField(features=['h2', 'h3', 'bold', 'italic', 'link'])`` would allow headings, bold / italic formatting and links, but not (for example) bullet lists or images. The ``register_rich_text_features`` hook allows new feature identifiers to be defined - see :ref:`rich_text_features` for details.


.. _insert_editor_css:

``insert_editor_css``
~~~~~~~~~~~~~~~~~~~~~

  Add additional CSS files or snippets to the page editor.

  .. code-block:: python

    from django.templatetags.static import static
    from django.utils.html import format_html

    from wagtail.core import hooks

    @hooks.register('insert_editor_css')
    def editor_css():
        return format_html(
            '<link rel="stylesheet" href="{}">',
            static('demo/css/vendor/font-awesome/css/font-awesome.min.css')
        )


.. _insert_global_admin_css:

``insert_global_admin_css``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add additional CSS files or snippets to all admin pages.

  .. code-block:: python

    from django.utils.html import format_html
    from django.templatetags.static import static

    from wagtail.core import hooks

    @hooks.register('insert_global_admin_css')
    def global_admin_css():
        return format_html('<link rel="stylesheet" href="{}">', static('my/wagtail/theme.css'))


.. _insert_editor_js:

``insert_editor_js``
~~~~~~~~~~~~~~~~~~~~

  Add additional JavaScript files or code snippets to the page editor.

  .. code-block:: python

    from django.utils.html import format_html, format_html_join
    from django.templatetags.static import static

    from wagtail.core import hooks

    @hooks.register('insert_editor_js')
    def editor_js():
        js_files = [
            'demo/js/jquery.raptorize.1.0.js',
        ]
        js_includes = format_html_join('\n', '<script src="{0}"></script>',
            ((static(filename),) for filename in js_files)
        )
        return js_includes + format_html(
            """
            <script>
                $(function() {
                    $('button').raptorize();
                });
            </script>
            """
        )


.. _insert_global_admin_js:

``insert_global_admin_js``
~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add additional JavaScript files or code snippets to all admin pages.

  .. code-block:: python

    from django.utils.html import format_html

    from wagtail.core import hooks

    @hooks.register('insert_global_admin_js')
    def global_admin_js():
        return format_html(
            '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r74/three.js"></script>',
        )


Editor workflow
---------------

Hooks for customising the way users are directed through the process of creating page content.


.. _after_create_page:

``after_create_page``
~~~~~~~~~~~~~~~~~~~~~

  Do something with a ``Page`` object after it has been saved to the database (as a published page or a revision). The callable passed to this hook should take a ``request`` object and a ``page`` object. The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the Explorer page for the new page's parent.

  .. code-block:: python

    from django.http import HttpResponse

    from wagtail.core import hooks

    @hooks.register('after_create_page')
    def do_after_page_create(request, page):
        return HttpResponse("Congrats on making content!", content_type="text/plain")


.. _before_create_page:

``before_create_page``
~~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "create page" view passing in the request, the parent page and page model class.

  The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object and skip the rest of the view.

  Unlike, ``after_create_page``, this is run both for both ``GET`` and ``POST`` requests.

  This can be used to completely override the editor on a per-view basis:

  .. code-block:: python

    from wagtail.core import hooks

    from .models import AwesomePage
    from .admin_views import edit_awesome_page

    @hooks.register('before_create_page')
    def before_create_page(request, parent_page, page_class):
        # Use a custom create view for the AwesomePage model
        if page_class == AwesomePage:
            return create_awesome_page(request, parent_page)

.. _after_delete_page:

``after_delete_page``
~~~~~~~~~~~~~~~~~~~~~

  Do something after a ``Page`` object is deleted. Uses the same behaviour as ``after_create_page``.


.. _before_delete_page:

``before_delete_page``
~~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "delete page" view passing in the request and the page object.

  Uses the same behaviour as ``before_create_page``.


.. _after_edit_page:

``after_edit_page``
~~~~~~~~~~~~~~~~~~~

  Do something with a ``Page`` object after it has been updated. Uses the same behaviour as ``after_create_page``.


.. _before_edit_page:

``before_edit_page``
~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "edit page" view passing in the request and the page object.

  Uses the same behaviour as ``before_create_page``.


.. _after_copy_page:

``after_copy_page``
~~~~~~~~~~~~~~~~~~~

  Do something with a ``Page`` object after it has been copied passing in the request, page object and the new copied page. Uses the same behaviour as ``after_create_page``.


.. _before_copy_page:

``before_copy_page``
~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "copy page" view passing in the request and the page object.

  Uses the same behaviour as ``before_create_page``.

.. _after_move_page:

``after_move_page``
~~~~~~~~~~~~~~~~~~~

  Do something with a ``Page`` object after it has been moved passing in the request and page object. Uses the same behaviour as ``after_create_page``.


.. _before_move_page:

``before_move_page``
~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "move page" view passing in the request, the page object and the destination page object.

  Uses the same behaviour as ``before_create_page``.

.. _register_page_action_menu_item:

``register_page_action_menu_item``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add an item to the popup menu of actions on the page creation and edit views. The callable passed to this hook must return an instance of ``wagtail.admin.action_menu.ActionMenuItem``. The following attributes and methods are available to be overridden on subclasses of ``ActionMenuItem``:

  :order: an integer (default 100) which determines the item's position in the menu. Can also be passed as a keyword argument to the object constructor
  :label: the displayed text of the menu item
  :get_url: a method which returns a URL for the menu item to link to; by default, returns ``None`` which causes the menu item to behave as a form submit button instead
  :name: value of the ``name`` attribute of the submit button, if no URL is specified
  :is_shown: a method which returns a boolean indicating whether the menu item should be shown; by default, true except when editing a locked page
  :template: path to a template to render to produce the menu item HTML
  :get_context: a method that returns a context dictionary to pass to the template
  :render_html: a method that returns the menu item HTML; by default, renders ``template`` with the context returned from ``get_context``
  :Media: an inner class defining Javascript and CSS to import when this menu item is shown - see `Django form media <https://docs.djangoproject.com/en/stable/topics/forms/media/>`_

  The ``get_url``, ``is_shown``, ``get_context`` and ``render_html`` methods all accept a request object and a context dictionary containing the following fields:

  :view: name of the current view: ``'create'``, ``'edit'`` or ``'revisions_revert'``
  :page: For ``view`` = ``'edit'`` or ``'revisions_revert'``, the page being edited
  :parent_page: For ``view`` = ``'create'``, the parent page of the page being created
  :user_page_permissions: a ``UserPagePermissionsProxy`` object for the current user, to test permissions against

  .. code-block:: python

    from wagtail.core import hooks
    from wagtail.admin.action_menu import ActionMenuItem

    class GuacamoleMenuItem(ActionMenuItem):
        label = "Guacamole"

        def get_url(self, request, context):
            return "https://www.youtube.com/watch?v=dNJdJIwCF_Y"


    @hooks.register('register_page_action_menu_item')
    def register_guacamole_menu_item():
        return GuacamoleMenuItem(order=10)


.. _construct_page_action_menu:

``construct_page_action_menu``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Modify the final list of action menu items on the page creation and edit views. The callable passed to this hook receives a list of ``ActionMenuItem`` objects, a request object and a context dictionary as per ``register_page_action_menu_item``, and should modify the list of menu items in-place.

  .. code-block:: python

    @hooks.register('construct_page_action_menu')
    def remove_submit_to_moderator_option(menu_items, request, context):
        menu_items[:] = [item for item in menu_items if item.name != 'action-submit']


.. _construct_wagtail_userbar:

``construct_wagtail_userbar``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add or remove items from the wagtail userbar. Add, edit, and moderation tools are provided by default. The callable passed into the hook must take the ``request`` object and a list of menu objects, ``items``. The menu item objects must have a ``render`` method which can take a ``request`` object and return the HTML string representing the menu item. See the userbar templates and menu item classes for more information.

  .. code-block:: python

    from wagtail.core import hooks

    class UserbarPuppyLinkItem:
        def render(self, request):
            return '<li><a href="http://cuteoverload.com/tag/puppehs/" ' \
                + 'target="_parent" class="action icon icon-wagtail">Puppies!</a></li>'

    @hooks.register('construct_wagtail_userbar')
    def add_puppy_link_item(request, items):
        return items.append( UserbarPuppyLinkItem() )


Admin workflow
--------------
Hooks for customising the way admins are directed through the process of editing users.


.. _after_create_user:

``after_create_user``
~~~~~~~~~~~~~~~~~~~~~

  Do something with a ``User`` object after it has been saved to the database.  The callable passed to this hook should take a ``request`` object and a ``user`` object. The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the User index page.

  .. code-block:: python

    from django.http import HttpResponse

    from wagtail.core import hooks

    @hooks.register('after_create_user')
    def do_after_page_create(request, user):
        return HttpResponse("Congrats on creating a new user!", content_type="text/plain")


.. _before_create_user:

``before_create_user``
~~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "create user" view passing in the request.

  The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object and skip the rest of the view.

  Unlike, ``after_create_user``, this is run both for both ``GET`` and ``POST`` requests.

  This can be used to completely override the user editor on a per-view basis:

  .. code-block:: python

    from wagtail.core import hooks

    from .models import AwesomePage
    from .admin_views import edit_awesome_page

    @hooks.register('before_create_user')
    def before_create_page(request):
        return HttpResponse("A user creation form", content_type="text/plain")



.. _after_delete_user:

``after_delete_user``
~~~~~~~~~~~~~~~~~~~~~

  Do something after a ``User`` object is deleted. Uses the same behaviour as ``after_create_user``.


.. _before_delete_user:

``before_delete_user``
~~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "delete user" view passing in the request and the user object.

  Uses the same behaviour as ``before_create_user``.


.. _after_edit_user:

``after_edit_user``
~~~~~~~~~~~~~~~~~~~

  Do something with a ``User`` object after it has been updated. Uses the same behaviour as ``after_create_user``.


.. _before_edit_user:

``before_edit_user``
~~~~~~~~~~~~~~~~~~~~~

  Called at the beginning of the "edit user" view passing in the request and the user object.

  Uses the same behaviour as ``before_create_user``.

Choosers
--------

.. _construct_page_chooser_queryset:

``construct_page_chooser_queryset``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when rendering the page chooser view, to allow the page listing QuerySet to be customised. The callable passed into the hook will receive the current page QuerySet and the request object, and must return a Page QuerySet (either the original one, or a new one).

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('construct_page_chooser_queryset')
    def show_my_pages_only(pages, request):
        # Only show own pages
        pages = pages.filter(owner=request.user)

        return pages


.. _construct_document_chooser_queryset:

``construct_document_chooser_queryset``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when rendering the document chooser view, to allow the document listing QuerySet to be customised. The callable passed into the hook will receive the current document QuerySet and the request object, and must return a Document QuerySet (either the original one, or a new one).

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('construct_document_chooser_queryset')
    def show_my_uploaded_documents_only(documents, request):
        # Only show uploaded documents
        documents = documents.filter(uploaded_by_user=request.user)

        return documents


.. _construct_image_chooser_queryset:

``construct_image_chooser_queryset``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when rendering the image chooser view, to allow the image listing QuerySet to be customised. The callable passed into the hook will receive the current image QuerySet and the request object, and must return a Document QuerySet (either the original one, or a new one).

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('construct_image_chooser_queryset')
    def show_my_uploaded_images_only(images, request):
        # Only show uploaded images
        images = images.filter(uploaded_by_user=request.user)

        return images


Page explorer
-------------

.. _construct_explorer_page_queryset:

``construct_explorer_page_queryset``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when rendering the page explorer view, to allow the page listing QuerySet to be customised. The callable passed into the hook will receive the parent page object, the current page QuerySet, and the request object, and must return a Page QuerySet (either the original one, or a new one).

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('construct_explorer_page_queryset')
    def show_my_profile_only(parent_page, pages, request):
        # If we're in the 'user-profiles' section, only show the user's own profile
        if parent_page.slug == 'user-profiles':
            pages = pages.filter(owner=request.user)

        return pages


.. _register_page_listing_buttons:

``register_page_listing_buttons``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add buttons to the actions list for a page in the page explorer. This is useful when adding custom actions to the listing, such as translations or a complex workflow.

  This example will add a simple button to the listing:

  .. code-block:: python

    from wagtail.admin import widgets as wagtailadmin_widgets

    @hooks.register('register_page_listing_buttons')
    def page_listing_buttons(page, page_perms, is_parent=False):
        yield wagtailadmin_widgets.PageListingButton(
            'A page listing button',
            '/goes/to/a/url/',
            priority=10
        )

  The ``priority`` argument controls the order the buttons are displayed in. Buttons are ordered from low to high priority, so a button with ``priority=10`` will be displayed before a button with ``priority=20``.


.. register_page_listing_more_buttons:

``register_page_listing_more_buttons``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

  Add buttons to the "More" dropdown menu for a page in the page explorer. This works similarly to the ``register_page_listing_buttons`` hook but is useful for lesser-used custom actions that are better suited for the dropdown.

  This example will add a simple button to the dropdown menu:

  .. code-block:: python

    from wagtail.admin import widgets as wagtailadmin_widgets

    @hooks.register('register_page_listing_more_buttons')
    def page_listing_more_buttons(page, page_perms, is_parent=False):
        yield wagtailadmin_widgets.Button(
            'A dropdown button',
            '/goes/to/a/url/',
            priority=60
        )

  The ``priority`` argument controls the order the buttons are displayed in the dropdown. Buttons are ordered from low to high priority, so a button with ``priority=10`` will be displayed before a button with ``priority=60``.


Buttons with dropdown lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^

  The admin widgets also provide ``ButtonWithDropdownFromHook``, which allows you to define a custom hook for generating a dropdown menu that gets attached to your button.

  Creating a button with a dropdown menu involves two steps. Firstly, you add your button to the ``register_page_listing_buttons`` hook, just like the example above.
  Secondly, you register a new hook that yields the contents of the dropdown menu.

  This example shows how Wagtail's default admin dropdown is implemented. You can also see how to register buttons conditionally, in this case by evaluating the ``page_perms``:

  .. code-block:: python

    from wagtail.admin import widgets as wagtailadmin_widgets

    @hooks.register('register_page_listing_buttons')
    def page_custom_listing_buttons(page, page_perms, is_parent=False):
        yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
            'More actions',
            hook_name='my_button_dropdown_hook',
            page=page,
            page_perms=page_perms,
            is_parent=is_parent,
            priority=50
        )

    @hooks.register('my_button_dropdown_hook')
    def page_custom_listing_more_buttons(page, page_perms, is_parent=False):
        if page_perms.can_move():
            yield wagtailadmin_widgets.Button('Move', reverse('wagtailadmin_pages:move', args=[page.id]), priority=10)
        if page_perms.can_delete():
            yield wagtailadmin_widgets.Button('Delete', reverse('wagtailadmin_pages:delete', args=[page.id]), priority=30)
        if page_perms.can_unpublish():
            yield wagtailadmin_widgets.Button('Unpublish', reverse('wagtailadmin_pages:unpublish', args=[page.id]), priority=40)



  The template for the dropdown button can be customised by overriding ``wagtailadmin/pages/listing/_button_with_dropdown.html``. The JavaScript that runs the dropdowns makes use of custom data attributes, so you should leave ``data-dropdown`` and ``data-dropdown-toggle`` in the markup if you customise it.


Page serving
------------

.. _before_serve_page:

``before_serve_page``
~~~~~~~~~~~~~~~~~~~~~

  Called when Wagtail is about to serve a page. The callable passed into the hook will receive the page object, the request object, and the ``args`` and ``kwargs`` that will be passed to the page's ``serve()`` method. If the callable returns an ``HttpResponse``, that response will be returned immediately to the user, and Wagtail will not proceed to call ``serve()`` on the page.

  .. code-block:: python

    from wagtail.core import hooks

    @hooks.register('before_serve_page')
    def block_googlebot(page, request, serve_args, serve_kwargs):
        if request.META.get('HTTP_USER_AGENT') == 'GoogleBot':
            return HttpResponse("<h1>bad googlebot no cookie</h1>")


Document serving
----------------

.. _before_serve_document:

``before_serve_document``
~~~~~~~~~~~~~~~~~~~~~~~~~

  Called when Wagtail is about to serve a document. The callable passed into the hook will receive the document object and the request object. If the callable returns an ``HttpResponse``, that response will be returned immediately to the user, instead of serving the document.
