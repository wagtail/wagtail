(admin_hooks)=

# Hooks

On loading, Wagtail will search for any app with the file `wagtail_hooks.py` and execute the contents. This provides a way to register your own functions to execute at certain points in Wagtail's execution, such as when a page is saved or when the main menu is constructed.

```{note}
Hooks are typically used to customise the view-level behaviour of the Wagtail admin and front-end.
For customisations that only deal with model-level behaviour - such as calling an external service when a page or document is added - it is often better to use [Django's signal mechanism](django:topics/signals) (see also: [Wagtail signals](signals)), as these are not dependent on a user taking a particular path through the admin interface.
```

Registering functions with a Wagtail hook is done through the `@hooks.register` decorator:

```python
from wagtail import hooks

@hooks.register('name_of_hook')
def my_hook_function(arg1, arg2...)
    # your code here
```

Alternatively, `hooks.register` can be called as an ordinary function, passing in the name of the hook and a handler function defined elsewhere:

```python
hooks.register('name_of_hook', my_hook_function)
```

If you need your hooks to run in a particular order, you can pass the `order` parameter. If order is not specified then the hooks proceed in the order given by `INSTALLED_APPS`. Wagtail uses hooks internally, too, so you need to be aware of order when overriding built-in Wagtail functionality (i.e. removing default summary items):

```python
@hooks.register('name_of_hook', order=1)  # This will run after every hook in the wagtail core
def my_hook_function(arg1, arg2...)
    # your code here

@hooks.register('name_of_hook', order=-1)  # This will run before every hook in the wagtail core
def my_other_hook_function(arg1, arg2...)
    # your code here

@hooks.register('name_of_hook', order=2)  # This will run after `my_hook_function`
def yet_another_hook_function(arg1, arg2...)
    # your code here
```

## Unit testing hooks

Hooks are usually registered on startup and can't be changed at runtime. But when writing unit tests, you might want to register a hook
function just for a single test or block of code and unregister it so that it doesn't run when other tests are run.

You can register hooks temporarily using the `hooks.register_temporarily` function, this can be used as both a decorator and a context
manager. Here's an example of how to register a hook function for just a single test:

```python
def my_hook_function():
    pass

class MyHookTest(TestCase):

    @hooks.register_temporarily('name_of_hook', my_hook_function)
    def test_my_hook_function(self):
        # Test with the hook registered here
        pass
```

And here's an example of registering a hook function for a single block of code:

```python
def my_hook_function():
    pass

with hooks.register_temporarily('name_of_hook', my_hook_function):
    # Hook is registered here
    ..

# Hook is unregistered here
```

If you need to register multiple hooks in a `with` block, you can pass the hooks in as a list of tuples:

```python
def my_hook(...):
    pass

def my_other_hook(...):
    pass

with hooks.register_temporarily([
    ('hook_name', my_hook),
    ('hook_name', my_other_hook),
]):
    # All hooks are registered here
    ..

# All hooks are unregistered here
```

The available hooks are listed below.

```{contents}
---
local:
depth: 1
---
```

## Admin modules

Hooks for building new areas of the admin interface (alongside pages, images, documents and so on).

(construct_homepage_panels)=

### `construct_homepage_panels`

Add or remove panels from the Wagtail admin homepage. The callable passed into this hook should take a `request` object and a list of panel objects, and should modify this list in-place as required. Panel objects are [](template_components) with an additional `order` property, an integer that determines the panel's position in the final ordered list. The default panels use integers between `100` and `300`.

```python
from django.utils.safestring import mark_safe

from wagtail.admin.ui.components import Component
from wagtail import hooks

class WelcomePanel(Component):
    order = 50

    def render_html(self, parent_context):
        return mark_safe("""
        <section class="panel summary nice-padding">
          <h3>No, but seriously -- welcome to the admin homepage.</h3>
        </section>
        """)

@hooks.register('construct_homepage_panels')
def add_another_welcome_panel(request, panels):
    panels.append(WelcomePanel())
```

(construct_homepage_summary_items)=

### `construct_homepage_summary_items`

Add or remove items from the 'site summary' bar on the admin homepage (which shows the number of pages and other object that exist on the site). The callable passed into this hook should take a `request` object and a list of summary item objects, and should modify this list in-place as required. Summary item objects are instances of `wagtail.admin.site_summary.SummaryItem`, which extends [the Component class](creating_template_components) with the following additional methods and properties:

```{eval-rst}
  .. method:: SummaryItem(request)

    Constructor; receives the request object its argument

  .. attribute:: order

    An integer that specifies the item's position in the sequence.

  .. method:: is_shown()

    Returns a boolean indicating whether the summary item should be shown on this request.
```

(construct_main_menu)=

### `construct_main_menu`

Called just before the Wagtail admin menu is output, to allow the list of menu items to be modified. The callable passed to this hook will receive a `request` object and a list of `menu_items`, and should modify `menu_items` in-place as required. Adding menu items should generally be done through the `register_admin_menu_item` hook instead - items added through `construct_main_menu` will not have their `is_shown` check applied.

```python
from wagtail import hooks

@hooks.register('construct_main_menu')
def hide_explorer_menu_item_from_frank(request, menu_items):
  if request.user.username == 'frank':
    menu_items[:] = [item for item in menu_items if item.name != 'explorer']
```

(describe_collection_contents)=

### `describe_collection_contents`

Called when Wagtail needs to find out what objects exist in a collection, if any. Currently this happens on the confirmation before deleting a collection, to ensure that non-empty collections cannot be deleted. The callable passed to this hook will receive a `collection` object, and should return either `None` (to indicate no objects in this collection), or a dict containing the following keys:

-   `count` - A numeric count of items in this collection
-   `count_text` - A human-readable string describing the number of items in this collection, such as "3 documents". (Sites with multi-language support should return a translatable string here, most likely using the `django.utils.translation.ngettext` function.)
-   `url` (optional) - A URL to an index page that lists the objects being described.

### `register_account_settings_panel`

Registers a new settings panel class to add to the "Account" view in the admin.

This hook can be added to a sub-class of `BaseSettingsPanel`. For example:

```python
from wagtail.admin.views.account import BaseSettingsPanel
from wagtail import hooks

@hooks.register('register_account_settings_panel')
class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    order = 500
    form_class = CustomSettingsForm
```

Alternatively, it can also be added to a function. For example, this function is equivalent to the above:

```python
from wagtail.admin.views.account import BaseSettingsPanel
from wagtail import hooks

class CustomSettingsPanel(BaseSettingsPanel):
    name = 'custom'
    title = "My custom settings"
    order = 500
    form_class = CustomSettingsForm

@hooks.register('register_account_settings_panel')
def register_custom_settings_panel(request, user, profile):
    return CustomSettingsPanel(request, user, profile)
```

More details about the options that are available can be found at [](custom_account_settings).

(register_account_menu_item)=

### `register_account_menu_item`

Add an item to the "More actions" tab on the "Account" page within the Wagtail admin.
The callable for this hook should return a dict with the keys
`url`, `label` and `help_text`. For example:

```python
from django.urls import reverse
from wagtail import hooks

@hooks.register('register_account_menu_item')
def register_account_delete_account(request):
    return {
        'url': reverse('delete-account'),
        'label': 'Delete account',
        'help_text': 'This permanently deletes your account.'
    }
```

(register_admin_menu_item)=

### `register_admin_menu_item`

Add an item to the Wagtail admin menu. The callable passed to this hook must return an instance of `wagtail.admin.menu.MenuItem`. New items can be constructed from the `MenuItem` class by passing in a `label` which will be the text in the menu item, and the URL of the admin page you want the menu item to link to (usually by calling `reverse()` on the admin view you've set up). Additionally, the following keyword arguments are accepted:

-   `name` - an internal name used to identify the menu item; defaults to the slugified form of the label.
-   `icon_name` - icon to display against the menu item; no defaults, optional, but should be set for top-level menu items so they can be identified when collapsed.
-   `classnames` - additional classnames applied to the link
-   `order` - an integer which determines the item's position in the menu

For menu items that are only available to superusers, the subclass `wagtail.admin.menu.AdminOnlyMenuItem` can be used in place of `MenuItem`.

`MenuItem` can be further subclassed to customise its initialisation or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (`wagtail/admin/menu.py`) for details.

```python
from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import MenuItem

@hooks.register('register_admin_menu_item')
def register_frank_menu_item():
  return MenuItem('Frank', reverse('frank'), icon_name='folder-inverse', order=10000)
```

(register_admin_urls)=

### `register_admin_urls`

Register additional admin page URLs. The callable fed into this hook should return a list of Django URL patterns which define the structure of the pages and endpoints of your extension to the Wagtail admin. For more about vanilla Django URLconfs and views, see [url dispatcher](django:topics/http/urls).

```python
from django.http import HttpResponse
from django.urls import path

from wagtail import hooks

def admin_view(request):
  return HttpResponse(
    "I have approximate knowledge of many things!",
    content_type="text/plain")

@hooks.register('register_admin_urls')
def urlconf_time():
  return [
    path('how_did_you_almost_know_my_name/', admin_view, name='frank'),
  ]
```

(register_group_permission_panel)=

### `register_group_permission_panel`

Add a new panel to the Groups form in the 'settings' area. The callable passed to this hook must return a ModelForm / ModelFormSet-like class, with a constructor that accepts a group object as its `instance` keyword argument, and which implements the methods `save`, `is_valid`, and `as_admin_panel` (which returns the HTML to be included on the group edit page).

(register_settings_menu_item)=

### `register_settings_menu_item`

As `register_admin_menu_item`, but registers menu items into the 'Settings' sub-menu rather than the top-level menu.

(construct_settings_menu)=

### `construct_settings_menu`

As `construct_main_menu`, but modifies the 'Settings' sub-menu rather than the top-level menu.

(register_reports_menu_item)=

### `register_reports_menu_item`

As `register_admin_menu_item`, but registers menu items into the 'Reports' sub-menu rather than the top-level menu.

(construct_reports_menu)=

### `construct_reports_menu`

As `construct_main_menu`, but modifies the 'Reports' sub-menu rather than the top-level menu.

(register_admin_search_area)=

### `register_admin_search_area`

Add an item to the Wagtail admin search "Other Searches". Behaviour of this hook is similar to `register_admin_menu_item`. The callable passed to this hook must return an instance of `wagtail.admin.search.SearchArea`. New items can be constructed from the `SearchArea` class by passing the following parameters:

-   `label` - text displayed in the "Other Searches" option box.
-   `name` - an internal name used to identify the search option; defaults to the slugified form of the label.
-   `url` - the URL of the target search page.
-   `classnames` - arbitrary CSS classnames applied to the link
-   `icon_name` - icon to display next to the label.
-   `attrs` - additional HTML attributes to apply to the link.
-   `order` - an integer which determines the item's position in the list of options.

Setting the URL can be achieved using reverse() on the target search page. The GET parameter 'q' will be appended to the given URL.

A template tag, `search_other` is provided by the `wagtailadmin_tags` template module. This tag takes a single, optional parameter, `current`, which allows you to specify the `name` of the search option currently active. If the parameter is not given, the hook defaults to a reverse lookup of the page's URL for comparison against the `url` parameter.

`SearchArea` can be subclassed to customise the HTML output, specify JavaScript files required by the option, or conditionally show or hide the item for specific requests (for example, to apply permission checks); see the source code (`wagtail/admin/search.py`) for details.

```python
from django.urls import reverse
from wagtail import hooks
from wagtail.admin.search import SearchArea

@hooks.register('register_admin_search_area')
def register_frank_search_area():
    return SearchArea('Frank', reverse('frank'), icon_name='folder-inverse', order=10000)
```

(register_permissions)=

### `register_permissions`

Return a QuerySet of `Permission` objects to be shown in the Groups administration area.

```python
  from django.contrib.auth.models import Permission
  from wagtail import hooks


  @hooks.register('register_permissions')
  def register_permissions():
      app = 'blog'
      model = 'extramodelset'

      return Permission.objects.filter(content_type__app_label=app, codename__in=[
          f"view_{model}", f"add_{model}", f"change_{model}", f"delete_{model}"
      ])
```

(filter_form_submissions_for_user)=

### `filter_form_submissions_for_user`

Allows access to form submissions to be customised on a per-user, per-form basis.

This hook takes two parameters:

-   The user attempting to access form submissions
-   A `QuerySet` of form pages

The hook must return a `QuerySet` containing a subset of these form pages which the user is allowed to access the submissions for.

For example, to prevent non-superusers from accessing form submissions:

```python
from wagtail import hooks


@hooks.register('filter_form_submissions_for_user')
def construct_forms_for_user(user, queryset):
    if not user.is_superuser:
        queryset = queryset.none()

    return queryset
```

## Editor interface

Hooks for customising the editing interface for pages and snippets.

(register_rich_text_features)=

### `register_rich_text_features`

Rich text fields in Wagtail work with a list of 'feature' identifiers that determine which editing controls are available in the editor, and which elements are allowed in the output; for example, a rich text field defined as `RichTextField(features=['h2', 'h3', 'bold', 'italic', 'link'])` would allow headings, bold / italic formatting and links, but not (for example) bullet lists or images. The `register_rich_text_features` hook allows new feature identifiers to be defined - see [](rich_text_features) for details.

(insert_editor_css)=

### `insert_editor_css`

Add additional CSS files or snippets to the page editor.

```python
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks

@hooks.register('insert_editor_css')
def editor_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static('demo/css/vendor/font-awesome/css/font-awesome.min.css')
    )
```

(insert_global_admin_css)=

### `insert_global_admin_css`

Add additional CSS files or snippets to all admin pages.

```python
from django.utils.html import format_html
from django.templatetags.static import static

from wagtail import hooks

@hooks.register('insert_global_admin_css')
def global_admin_css():
    return format_html('<link rel="stylesheet" href="{}">', static('my/wagtail/theme.css'))
```

(insert_editor_js)=

### `insert_editor_js`

Add additional JavaScript files or code snippets to the page editor.

```python
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe
from django.templatetags.static import static

from wagtail import hooks

@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'js/fireworks.js', # https://fireworks.js.org
    ]
    js_includes = format_html_join('\n', '<script src="{0}"></script>',
        ((static(filename),) for filename in js_files)
    )
    return js_includes + mark_safe(
        """
        <script>
            window.addEventListener('DOMContentLoaded', (event) => {
                var container = document.createElement('div');
                container.style.cssText = 'position: fixed; width: 100%; height: 100%; z-index: 100; top: 0; left: 0; pointer-events: none;';
                container.id = 'fireworks';
                document.getElementById('main').prepend(container);
                var options = { "acceleration": 1.2, "autoresize": true, "mouse": { "click": true, "max": 3 } };
                var fireworks = new Fireworks(document.getElementById('fireworks'), options);
                fireworks.start();
            });
        </script>
        """
    )
```

(insert_global_admin_js)=

### `insert_global_admin_js`

Add additional JavaScript files or code snippets to all admin pages.

```python
from django.utils.safestring import mark_safe

from wagtail import hooks

@hooks.register('insert_global_admin_js')
def global_admin_js():
    return mark_safe(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r74/three.js"></script>',
    )
```

(register_page_header_buttons)=

### `register_page_header_buttons`

Add buttons to the secondary dropdown menu in the page edit view. This works similarly to the `register_page_listing_buttons` hook.

This example will add a simple button to the secondary dropdown menu:

```python
from wagtail.admin import widgets as wagtailadmin_widgets

@hooks.register('register_page_header_buttons')
def page_header_buttons(page, page_perms, next_url=None):
    yield wagtailadmin_widgets.Button(
        'A dropdown button',
        '/goes/to/a/url/',
        priority=60
    )
```

The arguments passed to the hook are as follows:

-   `page` - the page object to generate the button for
-   `page_perms` - a `PagePermissionTester` object that can be queried to determine the current user's permissions on the given page
-   `next_url` - the URL that the linked action should redirect back to on completion of the action, if the view supports it

The `priority` argument controls the order the buttons are displayed in the dropdown. Buttons are ordered from low to high priority, so a button with `priority=10` will be displayed before a button with `priority=60`.

## Editor workflow

Hooks for customising the way users are directed through the process of creating page content.

(after_create_page)=

### `after_create_page`

Do something with a `Page` object after it has been saved to the database (as a published page or a revision). The callable passed to this hook should take a `request` object and a `page` object. The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the Explorer page for the new page's parent.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('after_create_page')
def do_after_page_create(request, page):
    return HttpResponse("Congrats on making content!", content_type="text/plain")
```

If you set attributes on a `Page` object, you should also call `save_revision()`, since the edit and index view pick up their data from the revisions table rather than the actual saved page record.

```python
  @hooks.register('after_create_page')
  def set_attribute_after_page_create(request, page):
      page.title = 'Persistent Title'
      new_revision = page.save_revision()
      if page.live:
          # page has been created and published at the same time,
          # so ensure that the updated title is on the published version too
          new_revision.publish()
```

(before_create_page)=

### `before_create_page`

Called at the beginning of the "create page" view passing in the request, the parent page and page model class.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

Unlike, `after_create_page`, this is run both for both `GET` and `POST` requests.

This can be used to completely override the editor on a per-view basis:

```python
from wagtail import hooks

from .models import AwesomePage
from .admin_views import edit_awesome_page

@hooks.register('before_create_page')
def before_create_page(request, parent_page, page_class):
    # Use a custom create view for the AwesomePage model
    if page_class == AwesomePage:
        return create_awesome_page(request, parent_page)
```

(after_delete_page)=

### `after_delete_page`

Do something after a `Page` object is deleted. Uses the same behaviour as `after_create_page`.

(before_delete_page)=

### `before_delete_page`

Called at the beginning of the "delete page" view passing in the request and the page object.

Uses the same behaviour as `before_create_page`, is is run both for both `GET` and `POST` requests.

```python
from django.shortcuts import redirect
from django.utils.html import format_html

from wagtail.admin import messages
from wagtail import hooks

from .models import AwesomePage


@hooks.register('before_delete_page')
def before_delete_page(request, page):
    """Block awesome page deletion and show a message."""

    if request.method == 'POST' and page.specific_class in [AwesomePage]:
        messages.warning(request, "Awesome pages cannot be deleted, only unpublished")
        return redirect('wagtailadmin_pages:delete', page.pk)
```

(after_edit_page)=

### `after_edit_page`

Do something with a `Page` object after it has been updated. Uses the same behaviour as `after_create_page`.

(before_edit_page)=

### `before_edit_page`

Called at the beginning of the "edit page" view passing in the request and the page object.

Uses the same behaviour as `before_create_page`.

(after_publish_page)=

### `after_publish_page`

Do something with a `Page` object after it has been published via page create view or page edit view.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(before_publish_page)=

### `before_publish_page`

Do something with a `Page` object before it has been published via page create view or page edit view.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(after_unpublish_page)=

### `after_unpublish_page`

Called after unpublish action in "unpublish" view passing in the request and the page object.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(before_unpublish_page)=

### `before_unpublish_page`

Called before unpublish action in "unpublish" view passing in the request and the page object.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(after_copy_page)=

### `after_copy_page`

Do something with a `Page` object after it has been copied passing in the request, page object and the new copied page. Uses the same behaviour as `after_create_page`.

(before_copy_page)=

### `before_copy_page`

Called at the beginning of the "copy page" view passing in the request and the page object.

Uses the same behaviour as `before_create_page`.

(after_move_page)=

### `after_move_page`

Do something with a `Page` object after it has been moved passing in the request and page object. Uses the same behaviour as `after_create_page`.

(before_move_page)=

### `before_move_page`

Called at the beginning of the "move page" view passing in the request, the page object and the destination page object.

Uses the same behaviour as `before_create_page`.

(before_convert_alias_page)=

### `before_convert_alias_page`

Called at the beginning of the `convert_alias` view, which is responsible for converting alias pages into normal Wagtail pages.

The request and the page being converted are passed in as arguments to the hook.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(after_convert_alias_page)=

### `after_convert_alias_page`

Do something with a `Page` object after it has been converted from an alias.

The request and the page that was just converted are passed in as arguments to the hook.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

(construct_translated_pages_to_cascade_actions)=

### `construct_translated_pages_to_cascade_actions`

Return additional pages to process in a synced tree setup.

This hook is only triggered on unpublishing a page when `WAGTAIL_I18N_ENABLED = True`.

The list of pages and the action are passed in as arguments to the hook.

The function should return a dictionary with the page from the pages list as key, and a list of additional pages to perform the action on.
We recommend they are non-aliased, direct translations of the pages from the function argument.

(register_page_action_menu_item)=

### `register_page_action_menu_item`

Add an item to the popup menu of actions on the page creation and edit views. The callable passed to this hook must return an instance of `wagtail.admin.action_menu.ActionMenuItem`. `ActionMenuItem` is a subclass of [Component](creating_template_components) and so the rendering of the menu item can be customised through `template_name`, `get_context_data`, `render_html` and `Media`. In addition, the following attributes and methods are available to be overridden:

-   `order` - an integer (default 100) which determines the item's position in the menu. Can also be passed as a keyword argument to the object constructor. The lowest-numbered item in this sequence will be selected as the default menu item; as standard, this is "Save draft" (which has an `order` of 0).
-   `label` - the displayed text of the menu item
-   `get_url` - a method which returns a URL for the menu item to link to; by default, returns `None` which causes the menu item to behave as a form submit button instead
-   `name` - value of the `name` attribute of the submit button, if no URL is specified
-   `icon_name` - icon to display against the menu item
-   `classname` - a `class` attribute value to add to the button element
-   `is_shown` - a method which returns a boolean indicating whether the menu item should be shown; by default, true except when editing a locked page

The `get_url`, `is_shown`, `get_context_data` and `render_html` methods all accept a context dictionary containing the following fields:

-   `view` - name of the current view: `'create'`, `'edit'` or `'revisions_revert'`
-   `page` - for `view` = `'edit'` or `'revisions_revert'`, the page being edited
-   `parent_page` - for `view` = `'create'`, the parent page of the page being created
-   `request` - the current request object
-   `user_page_permissions` - a `UserPagePermissionsProxy` object for the current user, to test permissions against

```python
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem

class GuacamoleMenuItem(ActionMenuItem):
    name = 'action-guacamole'
    label = "Guacamole"

    def get_url(self, context):
        return "https://www.youtube.com/watch?v=dNJdJIwCF_Y"


@hooks.register('register_page_action_menu_item')
def register_guacamole_menu_item():
    return GuacamoleMenuItem(order=10)
```

(construct_page_action_menu)=

### `construct_page_action_menu`

Modify the final list of action menu items on the page creation and edit views. The callable passed to this hook receives a list of `ActionMenuItem` objects, a request object and a context dictionary as per `register_page_action_menu_item`, and should modify the list of menu items in-place.

```python
@hooks.register('construct_page_action_menu')
def remove_submit_to_moderator_option(menu_items, request, context):
    menu_items[:] = [item for item in menu_items if item.name != 'action-submit']
```

The `construct_page_action_menu` hook is called after the menu items have been sorted by their order attributes, and so setting a menu item's order will have no effect at this point. Instead, items can be reordered by changing their position in the list, with the first item being selected as the default action. For example, to change the default action to Publish:

```python
@hooks.register('construct_page_action_menu')
def make_publish_default_action(menu_items, request, context):
    for (index, item) in enumerate(menu_items):
        if item.name == 'action-publish':
            # move to top of list
            menu_items.pop(index)
            menu_items.insert(0, item)
            break
```

(construct_page_listing_buttons)=

### `construct_page_listing_buttons`

Modify the final list of page listing buttons in the page explorer. The callable passed to this hook receives a list of `PageListingButton` objects, a page, a page perms object, and a context dictionary as per `register_page_listing_buttons`, and should modify the list of listing items in-place.

```python
@hooks.register('construct_page_listing_buttons')
def remove_page_listing_button_item(buttons, page, page_perms, is_parent=False, context=None):
    if is_parent:
        buttons.pop() # removes the last 'more' dropdown button on the parent page listing buttons
```

(construct_wagtail_userbar)=

### `construct_wagtail_userbar`

Add or remove items from the wagtail userbar. Add, edit, and moderation tools are provided by default. The callable passed into the hook must take the `request` object and a list of menu objects, `items`. The menu item objects must have a `render` method which can take a `request` object and return the HTML string representing the menu item. See the userbar templates and menu item classes for more information.

```python
from wagtail import hooks

class UserbarPuppyLinkItem:
    def render(self, request):
        return '<li><a href="http://cuteoverload.com/tag/puppehs/" ' \
            + 'target="_parent" role="menuitem" class="action icon icon-wagtail">Puppies!</a></li>'

@hooks.register('construct_wagtail_userbar')
def add_puppy_link_item(request, items):
    return items.append( UserbarPuppyLinkItem() )
```

## Admin workflow

Hooks for customising the way admins are directed through the process of editing users.

(after_create_user)=

### `after_create_user`

Do something with a `User` object after it has been saved to the database. The callable passed to this hook should take a `request` object and a `user` object. The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object. By default, Wagtail will instead redirect to the User index page.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('after_create_user')
def do_after_page_create(request, user):
    return HttpResponse("Congrats on creating a new user!", content_type="text/plain")
```

(before_create_user)=

### `before_create_user`

Called at the beginning of the "create user" view passing in the request.

The function does not have to return anything, but if an object with a `status_code` property is returned, Wagtail will use it as a response object and skip the rest of the view.

Unlike, `after_create_user`, this is run both for both `GET` and `POST` requests.

This can be used to completely override the user editor on a per-view basis:

```python
from django.http import HttpResponse

from wagtail import hooks

from .models import AwesomePage
from .admin_views import edit_awesome_page

@hooks.register('before_create_user')
def before_create_page(request):
    return HttpResponse("A user creation form", content_type="text/plain")
```

(after_delete_user)=

### `after_delete_user`

Do something after a `User` object is deleted. Uses the same behaviour as `after_create_user`.

(before_delete_user)=

### `before_delete_user`

Called at the beginning of the "delete user" view passing in the request and the user object.

Uses the same behaviour as `before_create_user`.

(after_edit_user)=

### `after_edit_user`

Do something with a `User` object after it has been updated. Uses the same behaviour as `after_create_user`.

(before_edit_user)=

### `before_edit_user`

Called at the beginning of the "edit user" view passing in the request and the user object.

Uses the same behaviour as `before_create_user`.

## Choosers

(construct_page_chooser_queryset)=

### `construct_page_chooser_queryset`

Called when rendering the page chooser view, to allow the page listing QuerySet to be customised. The callable passed into the hook will receive the current page QuerySet and the request object, and must return a Page QuerySet (either the original one, or a new one).

```python
from wagtail import hooks

@hooks.register('construct_page_chooser_queryset')
def show_my_pages_only(pages, request):
    # Only show own pages
    pages = pages.filter(owner=request.user)

    return pages
```

(construct_document_chooser_queryset)=

### `construct_document_chooser_queryset`

Called when rendering the document chooser view, to allow the document listing QuerySet to be customised. The callable passed into the hook will receive the current document QuerySet and the request object, and must return a Document QuerySet (either the original one, or a new one).

```python
from wagtail import hooks

@hooks.register('construct_document_chooser_queryset')
def show_my_uploaded_documents_only(documents, request):
    # Only show uploaded documents
    documents = documents.filter(uploaded_by_user=request.user)

    return documents
```

(construct_image_chooser_queryset)=

### `construct_image_chooser_queryset`

Called when rendering the image chooser view, to allow the image listing QuerySet to be customised. The callable passed into the hook will receive the current image QuerySet and the request object, and must return an Image QuerySet (either the original one, or a new one).

```python
from wagtail import hooks

@hooks.register('construct_image_chooser_queryset')
def show_my_uploaded_images_only(images, request):
    # Only show uploaded images
    images = images.filter(uploaded_by_user=request.user)

    return images
```

## Page explorer

(construct_explorer_page_queryset)=

### `construct_explorer_page_queryset`

Called when rendering the page explorer view, to allow the page listing QuerySet to be customised. The callable passed into the hook will receive the parent page object, the current page QuerySet, and the request object, and must return a Page QuerySet (either the original one, or a new one).

```python
from wagtail import hooks

@hooks.register('construct_explorer_page_queryset')
def show_my_profile_only(parent_page, pages, request):
    # If we're in the 'user-profiles' section, only show the user's own profile
    if parent_page.slug == 'user-profiles':
        pages = pages.filter(owner=request.user)

    return pages
```

(register_page_listing_buttons)=

### `register_page_listing_buttons`

Add buttons to the actions list for a page in the page explorer. This is useful when adding custom actions to the listing, such as translations or a complex workflow.

This example will add a simple button to the listing:

```python
from wagtail.admin import widgets as wagtailadmin_widgets

@hooks.register('register_page_listing_buttons')
def page_listing_buttons(page, page_perms, is_parent=False, next_url=None):>
    yield wagtailadmin_widgets.PageListingButton(
        'A page listing button',
        '/goes/to/a/url/',
        priority=10
    )
```

The arguments passed to the hook are as follows:

-   `page` - the page object to generate the button for
-   `page_perms` - a `PagePermissionTester` object that can be queried to determine the current user's permissions on the given page
-   `is_parent` - if true, this button is being rendered for the parent page being displayed at the top of the listing
-   `next_url` - the URL that the linked action should redirect back to on completion of the action, if the view supports it

The `priority` argument controls the order the buttons are displayed in. Buttons are ordered from low to high priority, so a button with `priority=10` will be displayed before a button with `priority=20`.

(register_page_listing_more_buttons)=

### `register_page_listing_more_buttons`

Add buttons to the "More" dropdown menu for a page in the page explorer. This works similarly to the `register_page_listing_buttons` hook but is useful for lesser-used custom actions that are better suited for the dropdown.

This example will add a simple button to the dropdown menu:

```python
from wagtail.admin import widgets as wagtailadmin_widgets

@hooks.register('register_page_listing_more_buttons')
def page_listing_more_buttons(page, page_perms, is_parent=False, next_url=None):
    yield wagtailadmin_widgets.Button(
        'A dropdown button',
        '/goes/to/a/url/',
        priority=60
    )
```

The arguments passed to the hook are as follows:

-   `page` - the page object to generate the button for
-   `page_perms` - a `PagePermissionTester` object that can be queried to determine the current user's permissions on the given page
-   `is_parent` - if true, this button is being rendered for the parent page being displayed at the top of the listing
-   `next_url` - the URL that the linked action should redirect back to on completion of the action, if the view supports it

The `priority` argument controls the order the buttons are displayed in the dropdown. Buttons are ordered from low to high priority, so a button with `priority=10` will be displayed before a button with `priority=60`.

#### Buttons with dropdown lists

The admin widgets also provide `ButtonWithDropdownFromHook`, which allows you to define a custom hook for generating a dropdown menu that gets attached to your button.

Creating a button with a dropdown menu involves two steps. Firstly, you add your button to the `register_page_listing_buttons` hook, just like the example above.
Secondly, you register a new hook that yields the contents of the dropdown menu.

This example shows how Wagtail's default admin dropdown is implemented. You can also see how to register buttons conditionally, in this case by evaluating the `page_perms`:

```python
from wagtail.admin import widgets as wagtailadmin_widgets

@hooks.register('register_page_listing_buttons')
def page_custom_listing_buttons(page, page_perms, is_parent=False, next_url=None):
    yield wagtailadmin_widgets.ButtonWithDropdownFromHook(
        'More actions',
        hook_name='my_button_dropdown_hook',
        page=page,
        page_perms=page_perms,
        is_parent=is_parent,
        next_url=next_url,
        priority=50
    )

@hooks.register('my_button_dropdown_hook')
def page_custom_listing_more_buttons(page, page_perms, is_parent=False, next_url=None):
    if page_perms.can_move():
        yield wagtailadmin_widgets.Button('Move', reverse('wagtailadmin_pages:move', args=[page.id]), priority=10)
    if page_perms.can_delete():
        yield wagtailadmin_widgets.Button('Delete', reverse('wagtailadmin_pages:delete', args=[page.id]), priority=30)
    if page_perms.can_unpublish():
        yield wagtailadmin_widgets.Button('Unpublish', reverse('wagtailadmin_pages:unpublish', args=[page.id]), priority=40)
```

The template for the dropdown button can be customised by overriding `wagtailadmin/pages/listing/_button_with_dropdown.html`. The JavaScript that runs the dropdowns makes use of custom data attributes, so you should leave `data-dropdown` and `data-dropdown-toggle` in the markup if you customise it.

## Page serving

(before_serve_page)=

### `before_serve_page`

Called when Wagtail is about to serve a page. The callable passed into the hook will receive the page object, the request object, and the `args` and `kwargs` that will be passed to the page's `serve()` method. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, and Wagtail will not proceed to call `serve()` on the page.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('before_serve_page')
def block_googlebot(page, request, serve_args, serve_kwargs):
    if request.META.get('HTTP_USER_AGENT') == 'GoogleBot':
        return HttpResponse("<h1>bad googlebot no cookie</h1>")
```

## Document serving

(before_serve_document)=

### `before_serve_document`

Called when Wagtail is about to serve a document. The callable passed into the hook will receive the document object and the request object. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, instead of serving the document. Note that this hook will be skipped if the [`WAGTAILDOCS_SERVE_METHOD`](wagtaildocs_serve_method) setting is set to `direct`.

## Snippets

Hooks for working with registered Snippets.

(after_edit_snippet)=

### `after_edit_snippet`

Called when a Snippet is edited. The callable passed into the hook will receive the model instance, the request object. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, and Wagtail will not proceed to call `redirect()` to the listing view.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('after_edit_snippet')
def after_snippet_update(request, instance):
    return HttpResponse(f"Congrats on editing a snippet with id {instance.pk}", content_type="text/plain")
```

(before_edit_snippet)=

### `before_edit_snippet`

Called at the beginning of the edit snippet view. The callable passed into the hook will receive the model instance, the request object. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, and Wagtail will not proceed to call `redirect()` to the listing view.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('before_edit_snippet')
def block_snippet_edit(request, instance):
    if isinstance(instance, RestrictedSnippet) and instance.prevent_edit:
        return HttpResponse("Sorry, you can't edit this snippet", content_type="text/plain")
```

(after_create_snippet)=

### `after_create_snippet`

Called when a Snippet is created. `after_create_snippet` and `after_edit_snippet` work in identical ways. The only difference is where the hook is called.

(before_create_snippet)=

### `before_create_snippet`

Called at the beginning of the create snippet view. Works in a similar way to `before_edit_snippet` except the model is passed as an argument instead of an instance.

(after_delete_snippet)=

### `after_delete_snippet`

Called when a Snippet is deleted. The callable passed into the hook will receive the model instance(s) as a queryset along with the request object. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, and Wagtail will not proceed to call `redirect()` to the listing view.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('after_delete_snippet')
def after_snippet_delete(request, instances):
    # "instances" is a QuerySet
    total = len(instances)
    return HttpResponse(f"{total} snippets have been deleted", content_type="text/plain")
```

(before_delete_snippet)=

### `before_delete_snippet`

Called at the beginning of the delete snippet view. The callable passed into the hook will receive the model instance(s) as a queryset along with the request object. If the callable returns an `HttpResponse`, that response will be returned immediately to the user, and Wagtail will not proceed to call `redirect()` to the listing view.

```python
from django.http import HttpResponse

from wagtail import hooks

@hooks.register('before_delete_snippet')
def before_snippet_delete(request, instances):
    # "instances" is a QuerySet
    total = len(instances)

    if request.method == 'POST':
      # Override the deletion behaviour
      instances.delete()

      return HttpResponse(f"{total} snippets have been deleted", content_type="text/plain")
```

(register_snippet_action_menu_item)=

### `register_snippet_action_menu_item`

Add an item to the popup menu of actions on the snippet creation and edit views.
The callable passed to this hook must return an instance of `wagtail.snippets.action_menu.ActionMenuItem`. `ActionMenuItem` is a subclass of [Component](creating_template_components) and so the rendering of the menu item can be customised through `template_name`, `get_context_data`, `render_html` and `Media`. In addition, the following attributes and methods are available to be overridden:

-   `order`- an integer (default 100) which determines the item's position in the menu. Can also be passed as a keyword argument to the object constructor. The lowest-numbered item in this sequence will be selected as the default menu item; as standard, this is "Save draft" (which has an`order` of 0).
-   `label` - the displayed text of the menu item
-   `get_url` - a method which returns a URL for the menu item to link to; by default, returns `None` which causes the menu item to behave as a form submit button instead
-   `name` - value of the `name` attribute of the submit button if no URL is specified
-   `icon_name` - icon to display against the menu item
-   `classname` - a `class` attribute value to add to the button element
-   `is_shown` - a method which returns a boolean indicating whether the menu item should be shown; by default, true except when editing a locked page

The `get_url`, `is_shown`, `get_context_data` and `render_html` methods all accept a context dictionary containing the following fields:

-   `view` - name of the current view: `'create'` or `'edit'`
-   `model` - the snippet's model class
-   `instance` - for `view` = `'edit'`, the instance being edited
-   `request` - the current request object

```python
from wagtail import hooks
from wagtail.snippets.action_menu import ActionMenuItem

class GuacamoleMenuItem(ActionMenuItem):
    name = 'action-guacamole'
    label = "Guacamole"

    def get_url(self, context):
        return "https://www.youtube.com/watch?v=dNJdJIwCF_Y"


@hooks.register('register_snippet_action_menu_item')
def register_guacamole_menu_item():
    return GuacamoleMenuItem(order=10)
```

(construct_snippet_action_menu)=

### `construct_snippet_action_menu`

Modify the final list of action menu items on the snippet creation and edit views.
The callable passed to this hook receives a list of `ActionMenuItem` objects, a request object and a context dictionary as per `register_snippet_action_menu_item`, and should modify the list of menu items in-place.

```python
@hooks.register('construct_snippet_action_menu')
def remove_delete_option(menu_items, request, context):
    menu_items[:] = [item for item in menu_items if item.name != 'delete']
```

The `construct_snippet_action_menu` hook is called after the menu items have been sorted by their order attributes, and so setting a menu item's order will have no effect at this point. Instead, items can be reordered by changing their position in the list, with the first item being selected as the default action. For example, to change the default action to Delete:

```python
@hooks.register('construct_snippet_action_menu')
def make_delete_default_action(menu_items, request, context):
    for (index, item) in enumerate(menu_items):
        if item.name == 'delete':
            # move to top of list
            menu_items.pop(index)
            menu_items.insert(0, item)
            break
```

(register_snippet_listing_buttons)=

### `register_snippet_listing_buttons`

Add buttons to the actions list for a snippet in the snippets listing. This is useful when adding custom actions to the listing, such as translations or a complex workflow.

This example will add a simple button to the listing:

```python
from wagtail.snippets import widgets as wagtailsnippets_widgets

@hooks.register('register_snippet_listing_buttons')
def snippet_listing_buttons(snippet, user, next_url=None):
    yield wagtailsnippets_widgets.SnippetListingButton(
        'A page listing button',
        '/goes/to/a/url/',
        priority=10
    )
```

The arguments passed to the hook are as follows:

-   `snippet` - the snippet object to generate the button for
-   `user` - the user who is viewing the snippets listing
-   `next_url` - the URL that the linked action should redirect back to on completion of the action, if the view supports it

The `priority` argument controls the order the buttons are displayed in. Buttons are ordered from low to high priority, so a button with `priority=10` will be displayed before a button with `priority=20`.

(construct_snippet_listing_buttons)=

### `construct_snippet_listing_buttons`

Modify the final list of snippet listing buttons. The callable passed to this hook receives a list of `SnippetListingButton` objects, a user, and a context dictionary as per `register_snippet_listing_buttons`, and should modify the list of menu items in-place.

```python
@hooks.register('construct_snippet_listing_buttons')
def remove_snippet_listing_button_item(buttons, snippet, user, context=None):
    buttons.pop()  # Removes the 'delete' button
```

## Bulk actions

Hooks for registering and customising bulk actions. See [](custom_bulk_actions) on how to write custom bulk actions.

(register_bulk_action)=

### `register_bulk_action`

Registers a new bulk action to add to the list of bulk actions in the explorer

This hook must be registered with a sub-class of `BulkAction` . For example:

```python
from wagtail.admin.views.bulk_action import BulkAction
from wagtail import hooks


@hooks.register("register_bulk_action")
class CustomBulkAction(BulkAction):
    display_name = _("Custom Action")
    action_type = "action"
    aria_label = _("Do custom action")
    template_name = "/path/to/template"
    models = [...]  # list of models the action should execute upon


    @classmethod
    def execute_action(cls, objects, **kwargs):
        for object in objects:
            do_something(object)
        return num_parent_objects, num_child_objects  # return the count of updated objects
```

(before_bulk_action)=

### `before_bulk_action`

Do something right before a bulk action is executed (before the `execute_action` method is called)

This hook can be used to return an HTTP response. For example:

```python
from wagtail import hooks

@hooks.register("before_bulk_action")
def hook_func(request, action_type, objects, action_class_instance):
  if action_type == 'delete':
    return HttpResponse(f"{len(objects)} objects would be deleted", content_type="text/plain")
```

(after_bulk_action)=

### `after_bulk_action`

Do something right after a bulk action is executed (after the `execute_action` method is called)

This hook can be used to return an HTTP response. For example:

```python
from wagtail import hooks

@hooks.register("after_bulk_action")
def hook_func(request, action_type, objects, action_class_instance):
  if action_type == 'delete':
    return HttpResponse(f"{len(objects)} objects have been deleted", content_type="text/plain")
```

## Audit log

(register_log_actions)=

### `register_log_actions`

See [](audit_log)

To add new actions to the registry, call the `register_action` method with the action type, its label and the message to be displayed in administrative listings.

```python
from django.utils.translation import gettext_lazy as _

from wagtail import hooks

@hooks.register('register_log_actions')
def additional_log_actions(actions):
    actions.register_action('wagtail_package.echo', _('Echo'), _('Sent an echo'))
```

Alternatively, for a log message that varies according to the log entry's data, create a subclass of `wagtail.log_actions.LogFormatter` that overrides the `format_message` method, and use `register_action` as a decorator on that class:

```python
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.log_actions import LogFormatter

@hooks.register('register_log_actions')
def additional_log_actions(actions):
    @actions.register_action('wagtail_package.greet_audience')
    class GreetingActionFormatter(LogFormatter):
        label = _('Greet audience')

        def format_message(self, log_entry):
            return _('Hello %(audience)s') % {
                'audience': log_entry.data['audience'],
            }
```

```{versionchanged} 2.15
The ``LogFormatter`` class was introduced. Previously, dynamic messages were achieved by passing a callable as the ``message`` argument to ``register_action``.
```
