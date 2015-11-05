
.. _admin_hooks:

Hooks
-----

On loading, Wagtail will search for any app with the file ``wagtail_hooks.py`` and execute the contents. This provides a way to register your own functions to execute at certain points in Wagtail's execution, such as when a ``Page`` object is saved or when the main menu is constructed.

Registering functions with a Wagtail hook is done through the ``@hooks.register`` decorator:

.. code-block:: python

  from wagtail.wagtailcore import hooks

  @hooks.register('name_of_hook')
  def my_hook_function(arg1, arg2...)
      # your code here


Alternatively, ``hooks.register`` can be called as an ordinary function, passing in the name of the hook and a handler function defined elsewhere:

.. code-block:: python

  hooks.register('name_of_hook', my_hook_function)


The available hooks are:

.. _before_serve_page:

``before_serve_page``

  Called when Wagtail is about to serve a page. The callable passed into the hook will receive the page object, the request object, and the ``args`` and ``kwargs`` that will be passed to the page's ``serve()`` method. If the callable returns an ``HttpResponse``, that response will be returned immediately to the user, and Wagtail will not proceed to call ``serve()`` on the page.

  .. code-block:: python

    from wagtail.wagtailcore import hooks

    @hooks.register('before_serve_page')
    def block_googlebot(page, request, serve_args, serve_kwargs):
        if request.META.get('HTTP_USER_AGENT') == 'GoogleBot':
            return HttpResponse("<h1>bad googlebot no cookie</h1>")


.. _construct_wagtail_userbar:

.. versionchanged:: 1.0

   The hook was renamed from ``construct_wagtail_edit_bird``

``construct_wagtail_userbar``
  Add or remove items from the wagtail userbar. Add, edit, and moderation tools are provided by default. The callable passed into the hook must take the ``request`` object and a list of menu objects, ``items``. The menu item objects must have a ``render`` method which can take a ``request`` object and return the HTML string representing the menu item. See the userbar templates and menu item classes for more information.

  .. code-block:: python

    from wagtail.wagtailcore import hooks

    class UserbarPuppyLinkItem(object):
      def render(self, request):
        return '<li><a href="http://cuteoverload.com/tag/puppehs/" ' \
        + 'target="_parent" class="action icon icon-wagtail">Puppies!</a></li>'

    @hooks.register('construct_wagtail_userbar')
    def add_puppy_link_item(request, items):
      return items.append( UserbarPuppyLinkItem() )


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

    @hooks.register('construct_homepage_panels')
    def add_another_welcome_panel(request, panels):
      return panels.append( WelcomePanel() )


.. _construct_homepage_summary_items:

``construct_homepage_summary_items``
  .. versionadded:: 1.0

  Add or remove items from the 'site summary' bar on the admin homepage (which shows the number of pages and other object that exist on the site). The callable passed into this hook should take a ``request`` object and a list of ``SummaryItem`` objects to be modified as required. These objects have a ``render()`` method, which returns an HTML string, and an ``order`` property, which is an integer that specifies the order in which the items will appear.


.. _after_create_page:

``after_create_page``
  Do something with a ``Page`` object after it has been saved to the database (as a published page or a revision). The callable passed to this hook should take a ``request`` object and a ``page`` object. The function does not have to return anything, but if an object with a ``status_code`` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the Explorer page for the new page's parent.

  .. code-block:: python

    from django.http import HttpResponse

    from wagtail.wagtailcore import hooks

    @hooks.register('after_create_page')
    def do_after_page_create(request, page):
      return HttpResponse("Congrats on making content!", content_type="text/plain")


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

    @hooks.register('register_admin_urls')
    def urlconf_time():
      return [
        url(r'^how_did_you_almost_know_my_name/$', admin_view, name='frank' ),
      ]

.. _register_admin_menu_item:

``register_admin_menu_item``

  Add an item to the Wagtail admin menu. The callable passed to this hook must return an instance of ``wagtail.wagtailadmin.menu.MenuItem``. New items can be constructed from the ``MenuItem`` class by passing in a ``label`` which will be the text in the menu item, and the URL of the admin page you want the menu item to link to (usually by calling ``reverse()`` on the admin view you've set up). Additionally, the following keyword arguments are accepted:

  :name: an internal name used to identify the menu item; defaults to the slugified form of the label.
  :classnames: additional classnames applied to the link, used to give it an icon
  :attrs: additional HTML attributes to apply to the link
  :order: an integer which determines the item's position in the menu

  ``MenuItem`` can be subclassed to customise the HTML output, specify Javascript files required by the menu item, or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (``wagtail/wagtailadmin/menu.py``) for details.

  .. code-block:: python

    from django.core.urlresolvers import reverse

    from wagtail.wagtailcore import hooks
    from wagtail.wagtailadmin.menu import MenuItem

    @hooks.register('register_admin_menu_item')
    def register_frank_menu_item():
      return MenuItem('Frank', reverse('frank'), classnames='icon icon-folder-inverse', order=10000)

.. _register_settings_menu_item:

``register_settings_menu_item``
  .. versionadded:: 0.7

  As ``register_admin_menu_item``, but registers menu items into the 'Settings' sub-menu rather than the top-level menu.

.. _construct_main_menu:

``construct_main_menu``
  Called just before the Wagtail admin menu is output, to allow the list of menu items to be modified. The callable passed to this hook will receive a ``request`` object and a list of ``menu_items``, and should modify ``menu_items`` in-place as required. Adding menu items should generally be done through the ``register_admin_menu_item`` hook instead - items added through ``construct_main_menu`` will be missing any associated Javascript includes, and their ``is_shown`` check will not be applied.

  .. code-block:: python

    from wagtail.wagtailcore import hooks

    @hooks.register('construct_main_menu')
    def hide_explorer_menu_item_from_frank(request, menu_items):
      if request.user.username == 'frank':
        menu_items[:] = [item for item in menu_items if item.name != 'explorer']

.. _register_admin_search_area:

``register_admin_search_area``

  Add an item to the Wagtail admin search "Other Searches". Behaviour of this hook is similar to ``register_admin_menu_item``. The callable passed to this hook must return an instance of ``wagtail.wagtailadmin.search.SearchArea``. New items can be constructed from the ``SearchArea`` class by passing the following parameters:

  :label: text displayed in the "Other Searches" option box.
  :name: an internal name used to identify the search option; defaults to the slugified form of the label.
  :url: the URL of the target search page.
  :classnames: additional CSS classnames applied to the link, used to give it an icon.
  :attrs: additional HTML attributes to apply to the link.
  :order: an integer which determines the item's position in the list of options.

  Setting the URL can be achieved using reverse() on the target search page. The GET parameter 'q' will be appended to the given URL.

  A template tag, ``search_other`` is provided by the ``wagtailadmin_tags`` template module. This tag takes a single, optional parameter, ``current``, which allows you to specify the ``name`` of the search option currently active. If the parameter is not given, the hook defaults to a reverse lookup of the page's URL for comparison against the ``url`` parameter.


  ``SearchArea`` can be subclassed to customise the HTML output, specify Javascript files required by the option, or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (``wagtail/wagtailadmin/search.py``) for details.

  .. code-block:: python

    from django.core.urlresolvers import reverse
    from wagtail.wagtailcore import hooks
    from wagtail.wagtailadmin.search import SearchArea

    @hooks.register('register_admin_search_area')
    def register_frank_search_area():
      return SearchArea('Frank', reverse('frank'), classnames='icon icon-folder-inverse', order=10000)

.. _insert_editor_js:

``insert_editor_js``
  Add additional Javascript files or code snippets to the page editor. Output must be compatible with ``compress``, as local static includes or string.

  .. code-block:: python

    from django.utils.html import format_html, format_html_join
    from django.conf import settings

    from wagtail.wagtailcore import hooks

    @hooks.register('insert_editor_js')
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


.. _insert_editor_css:

``insert_editor_css``
  Add additional CSS or SCSS files or snippets to the page editor. Output must be compatible with ``compress``, as local static includes or string.

  .. code-block:: python

    from django.utils.html import format_html
    from django.conf import settings

    from wagtail.wagtailcore import hooks

    @hooks.register('insert_editor_css')
    def editor_css():
      return format_html('<link rel="stylesheet" href="' \
      + settings.STATIC_URL \
      + 'demo/css/vendor/font-awesome/css/font-awesome.min.css">')

.. _construct_whitelister_element_rules:

``construct_whitelister_element_rules``

  Customise the rules that define which HTML elements are allowed in rich text areas. By default only a limited set of HTML elements and attributes are whitelisted - all others are stripped out. The callables passed into this hook must return a dict, which maps element names to handler functions that will perform some kind of manipulation of the element. These handler functions receive the element as a `BeautifulSoup <http://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_ Tag object.

  The ``wagtail.wagtailcore.whitelist`` module provides a few helper functions to assist in defining these handlers: ``allow_without_attributes``, a handler which preserves the element but strips out all of its attributes, and ``attribute_rule`` which accepts a dict specifying how to handle each attribute, and returns a handler function. This dict will map attribute names to either True (indicating that the attribute should be kept), False (indicating that it should be dropped), or a callable (which takes the initial attribute value and returns either a final value for the attribute, or None to drop the attribute).

  For example, the following hook function will add the ``<blockquote>`` element to the whitelist, and allow the ``target`` attribute on ``<a>`` elements:

  .. code-block:: python

    from wagtail.wagtailcore import hooks
    from wagtail.wagtailcore.whitelist import attribute_rule, check_url, allow_without_attributes

    @hooks.register('construct_whitelister_element_rules')
    def whitelister_element_rules():
        return {
            'blockquote': allow_without_attributes,
            'a': attribute_rule({'href': check_url, 'target': True}),
        }

.. _register_permissions:

``register_permissions``
  .. versionadded:: 0.7

  Return a queryset of Permission objects to be shown in the Groups administration area.
