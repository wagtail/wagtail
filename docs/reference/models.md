# Model reference

```{eval-rst}
.. module:: wagtail.models
```

This document contains reference information for the model classes inside the `wagtail.models` module.

(page_model_ref)=

## `Page`

### Database fields

```{eval-rst}
.. class:: Page

    .. attribute:: title

        (text)

        Human-readable title of the page.

    .. attribute:: draft_title

        (text)

        Human-readable title of the page, incorporating any changes that have been made in a draft edit (in contrast to the ``title`` field, which for published pages will be the title as it exists in the current published version).

    .. attribute:: slug

        (text)

        This is used for constructing the page's URL.

        For example: ``http://domain.com/blog/[my-slug]/``

    .. attribute:: content_type

        (foreign key to ``django.contrib.contenttypes.models.ContentType``)

        A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` object that represents the specific model of this page.

    .. attribute:: live

        (boolean)

        A boolean that is set to ``True`` if the page is published.

        Note: this field defaults to ``True`` meaning that any pages that are created programmatically will be published by default.

    .. attribute:: has_unpublished_changes

        (boolean)

        A boolean that is set to ``True`` when the page is either in draft or published with draft changes.

    .. attribute:: owner

        (foreign key to user model)

        A foreign key to the user that created the page.

    .. attribute:: first_published_at

        (date/time)

        The date/time when the page was first published.

    .. attribute:: last_published_at

        (date/time)

        The date/time when the page was last published.

    .. attribute:: seo_title

        (text)

        Alternate SEO-crafted title, for use in the page's ``<title>`` HTML tag.

    .. attribute:: search_description

        (text)

        SEO-crafted description of the content, used for search indexing. This is also suitable for the page's ``<meta name="description">`` HTML tag.

    .. attribute:: show_in_menus

        (boolean)

        Toggles whether the page should be included in site-wide menus, and is shown in the ``promote_panels`` within the Page editor.

        Wagtail does not include any menu implementation by default, which means that this field will not do anything in the front facing content unless built that way in a specific Wagtail installation.

        However, this is used by the :meth:`~wagtail.query.PageQuerySet.in_menu` QuerySet filter to make it easier to query for pages that use this field.

        Defaults to ``False`` and can be overridden on the model with ``show_in_menus_default = True``.

        .. note::

            To set the global default for all pages, set ``Page.show_in_menus_default = True`` once where you first import the ``Page`` model.

    .. attribute:: locked

        (boolean)

        When set to ``True``, the Wagtail editor will not allow any users to edit
        the content of the page.

        If ``locked_by`` is also set, only that user can edit the page.

    .. attribute:: locked_by

        (foreign key to user model)

        The user who has currently locked the page. Only this user can edit the page.

        If this is ``None`` when ``locked`` is ``True``, nobody can edit the page.

    .. attribute:: locked_at

        (date/time)

        The date/time when the page was locked.

    .. attribute:: alias_of

        (foreign key to another page)

        If set, this page is an alias of the page referenced in this field.

    .. attribute:: locale

        (foreign key to Locale)

        This foreign key links to the ``Locale`` object that represents the page language.

    .. attribute:: translation_key

        (uuid)

        A UUID that is shared between translations of a page. These are randomly generated
        when a new page is created and copied when a translation of a page is made.

        A ``translation_key`` value can only be used on one page in each locale.
```

### Methods and properties

In addition to the model fields provided, `Page` has many properties and methods that you may wish to reference, use, or override in creating your own models.

```{note}
See also [django-treebeard](inv:treebeard:std:doc#index)'s [node API](inv:treebeard:std:doc#api). ``Page`` is a subclass of [materialized path tree](inv:treebeard:std:doc#mp_tree) nodes.
```

```{eval-rst}
.. class:: Page
    :no-index:

    .. automethod:: get_specific

    .. autoattribute:: specific

    .. autoattribute:: specific_deferred

    .. autoattribute:: specific_class

    .. autoattribute:: cached_content_type

    .. autoattribute:: page_type_display_name

    .. automethod:: get_url

    .. automethod:: get_full_url

    .. autoattribute:: full_url

    .. automethod:: relative_url

    .. automethod:: get_site

    .. automethod:: get_url_parts

    .. automethod:: route

    .. automethod:: serve

    .. automethod:: route_for_request

    .. automethod:: find_for_request

    .. method:: get_default_privacy_setting(request)

        Set the default privacy setting for the page.

        The method must return a dictionary with at least a 'type' key. The value must be one of the following values from :class:`~wagtail.models.PageViewRestriction`'s :attr:`~wagtail.models.PageViewRestriction.restriction_type`:

        - ``BaseViewRestriction.NONE``: The page is public and can be accessed by anyone. (default) - '{"type": BaseViewRestriction.NONE}'

        - ``BaseViewRestriction.LOGIN``: The page is private and can only be accessed by authenticated users. - '{"type": BaseViewRestriction.LOGIN}'

        - ``BaseViewRestriction.PASSWORD``: The page is private and can only be accessed by users with a shared password. (requires additional ``password`` key in the dictionary) - '{"type": BaseViewRestriction.PASSWORD, "password": "P@ssw0rd123!"}'

        - ``BaseViewRestriction.GROUPS``: The page is private and can only be accessed by users in specific groups. (requires additional ``groups`` key with list of Group objects) - '{"type": BaseViewRestriction.GROUPS, "groups": [moderators, editors]}'

        Example

        .. code-block:: python

            class BreadsIndexPage(Page):
                #...

                def get_default_privacy_setting(request):
                    from wagtail.models import BaseViewRestriction
                    # if the editor has the foo.add_bar permission set the default to groups with the moderators and editors group checked
                    if request.user.has_perm("foo.add_bar"):
                        moderators = Group.objects.filter(name="Moderators").first()
                        editors = Group.objects.filter(name="Editors").first()
                        return {"type": BaseViewRestriction.GROUPS, "groups": [moderators,editors]}
                    else:
                        return {"type": BaseViewRestriction.NONE}


    .. autoattribute:: context_object_name

        Custom name for page instance in page's ``Context``.

    .. automethod:: get_context

    .. automethod:: get_template

    .. automethod:: get_admin_display_title

    .. autoattribute:: allowed_http_methods

        When customizing this attribute, developers are encouraged to use values from Python's built-in ``http.HTTPMethod`` enum in the list, as it is more robust, and makes use of values that already exist in memory. For example:

        .. code-block:: python

            from http import HTTPMethod

            class MyPage(Page):
                allowed_http_methods = [HTTPMethod.GET, HTTPMethod.OPTIONS]

        The ``http.HTTPMethod`` enum wasn't added until Python 3.11, so if your project uses an older version of Python, you can use uppercase strings instead. For example:

        .. code-block:: python

            class MyPage(Page):
                allowed_http_methods = ["GET", "OPTIONS"]

    .. automethod:: check_request_method

    .. automethod:: handle_options_request

    .. autoattribute:: preview_modes

    .. autoattribute:: default_preview_mode

    .. autoattribute:: preview_sizes

    .. autoattribute:: default_preview_size

    .. automethod:: serve_preview

    .. automethod:: get_parent

    .. automethod:: get_children

    .. automethod:: get_ancestors

    .. automethod:: get_descendants

    .. automethod:: get_siblings

    .. automethod:: get_translations

    .. automethod:: get_translation

    .. automethod:: get_translation_or_none

    .. automethod:: has_translation

    .. automethod:: copy_for_translation

    .. method:: get_admin_default_ordering

       Returns the default sort order for child pages to be sorted in viewing the admin pages index and not seeing search results.

       The following sort orders are available:

       - ``'content_type'``
       - ``'-content_type'``
       - ``'latest_revision_created_at'``
       - ``'-latest_revision_created_at'``
       - ``'live'``
       - ``'-live'``
       - ``'ord'``
       - ``'title'``
       - ``'-title'``

       For example to make a page sort by title for all the child pages only if there are < 20 pages.

       .. code-block:: python

           class BreadsIndexPage(Page):
               def get_admin_default_ordering(self):
                   if Page.objects.child_of(self).count() < 20:
                       return 'title'
                   return self.admin_default_ordering

    .. attribute:: admin_default_ordering

        An attribute version for the method ``get_admin_default_ordering()``, defaults to ``'-latest_revision_created_at'``.

    .. autoattribute:: localized

    .. autoattribute:: localized_draft

    .. attribute:: search_fields

        A list of fields to be indexed by the search engine. See Search docs :ref:`wagtailsearch_indexing_fields`

    .. attribute:: subpage_types

        A list of page models which can be created as children of this page type. For example, a ``BlogIndex`` page might allow a ``BlogPage`` as a child, but not a ``JobPage``:

        .. code-block:: python

            class BlogIndex(Page):
                subpage_types = ['mysite.BlogPage', 'mysite.BlogArchivePage']

        The creation of child pages can be blocked altogether for a given page by setting its subpage_types attribute to an empty array:

        .. code-block:: python

            class BlogPage(Page):
                subpage_types = []

    .. attribute:: parent_page_types

        A list of page models which are allowed as parent page types. For example, a ``BlogPage`` may only allow itself to be created below the ``BlogIndex`` page:

        .. code-block:: python

            class BlogPage(Page):
                parent_page_types = ['mysite.BlogIndexPage']

        Pages can block themselves from being created at all by setting parent_page_types to an empty array (this is useful for creating unique pages that should only be created once):

        .. code-block:: python

            class HiddenPage(Page):
                parent_page_types = []

        To allow for a page to be only created under the root page (for example for ``HomePage`` models) set the ``parent_page_type`` to ``['wagtailcore.Page']``.

        .. code-block:: python

            class HomePage(Page):
                parent_page_types = ['wagtailcore.Page']

    .. automethod:: can_exist_under

    .. automethod:: can_create_at

    .. automethod:: can_move_to

    .. automethod:: get_route_paths

    .. attribute:: password_required_template

        Defines which template file should be used to render the login form for Protected pages using this model. This overrides the default, defined using ``WAGTAIL_PASSWORD_REQUIRED_TEMPLATE`` in your settings. See :ref:`private_pages`

    .. attribute:: is_creatable

        Controls if this page can be created through the Wagtail administration. Defaults to ``True``, and is not inherited by subclasses. This is useful when using :ref:`multi-table inheritance <django:meta-and-multi-table-inheritance>`, to stop the base model from being created as an actual page.

    .. attribute:: max_count

        Controls the maximum number of pages of this type that can be created through the Wagtail administration interface. This is useful when needing "allow at most 3 of these pages to exist", or for singleton pages.

    .. attribute:: max_count_per_parent

        Controls the maximum number of pages of this type that can be created under any one parent page.

    .. attribute:: private_page_options

        Controls what privacy options are available for the page type.

       The following options are available:

       - ``'password'`` - Can restrict to use a shared password
       - ``'groups'`` - Can restrict to users in specific groups
       - ``'login'`` - Can restrict to logged in users

        .. code-block:: python

            class BreadPage(Page):
                ...

                # default
                private_page_options = ['password', 'groups', 'login']

                # disable shared password
                private_page_options = ['groups', 'login']

                # only shared password
                private_page_options = ['password']

                # no privacy options for this page model
                private_page_options = []

    .. attribute:: exclude_fields_in_copy

        An array of field names that will not be included when a Page is copied.
        Useful when you have relations that do not use ``ClusterableModel`` or should not be copied.

        .. code-block:: python

            class BlogPage(Page):
                exclude_fields_in_copy = ['special_relation', 'custom_uuid']

        The following fields will always be excluded in a copy - `['id', 'path', 'depth', 'numchild', 'url_path', 'path']`.

    .. attribute:: base_form_class

        The form class is used as a base for editing Pages of this type in the Wagtail page editor.
        This attribute can be set on a model to customize the Page editor form.
        Forms must be a subclass of :class:`~wagtail.admin.forms.WagtailAdminPageForm`.
        See :ref:`custom_edit_handler_forms` for more information.

    .. automethod:: with_content_json

    .. automethod:: save

    .. automethod:: copy

    .. method:: move(new_parent, pos=None)

        Move a page and all its descendants to a new parent.
        See :meth:`django-treebeard <treebeard.mp_tree.MP_Node.move>` for more information.


    .. automethod:: create_alias

    .. automethod:: update_aliases

    .. automethod:: get_cache_key_components

    .. autoattribute:: cache_key
```

(site_model_ref)=

## `Site`

The `Site` model is useful for multi-site installations as it allows an administrator to configure which part of the tree to use for each hostname that the server responds on.

The {meth}`~wagtail.models.Site.find_for_request` function returns the Site object that will handle the given HTTP request.

### Database fields

```{eval-rst}
.. class:: Site

    .. attribute:: hostname

        (text)

        This is the hostname of the site, excluding the scheme, port, and path.

        For example: ``www.mysite.com``

        .. note::

            If you're looking for how to get the root url of a site, use the :attr:`~Site.root_url` attribute.

    .. attribute:: port

        (number)

        This is the port number that the site responds on.

    .. attribute:: site_name

        (text - optional)

        A human-readable name for the site. This is not used by Wagtail itself, but is suitable for use on the site front-end, such as in ``<title>`` elements.

        For example: ``Rod's World of Birds``

    .. attribute:: root_page

        (foreign key to :class:`~wagtail.models.Page`)

        This is a link to the root page of the site. This page will be what appears at the ``/`` URL on the site and would usually be a homepage.

    .. attribute:: is_default_site

        (boolean)

        This is set to ``True`` if the site is the default. Only one site can be the default.

        The default site is used as a fallback in situations where a site with the required hostname/port couldn't be found.
```

### Methods and properties

```{eval-rst}
.. class:: Site
    :no-index:

    .. automethod:: find_for_request

    .. autoattribute:: root_url

        This returns the URL of the site. It is calculated from the :attr:`~Site.hostname` and the :attr:`~Site.port` fields.

        The scheme part of the URL is calculated based on value of the :attr:`~Site.port` field:

        - 80 = ``http://``
        - 443 = ``https://``
        - Everything else will use the ``http://`` scheme and the port will be appended to the end of the hostname (for example ``http://mysite.com:8000/``)

    .. automethod:: get_site_root_paths
```

(locale_model_ref)=

## `Locale`

The `Locale` model defines the set of languages and/or locales that can be used on a site.
Each `Locale` record corresponds to a "language code" defined in the {ref}`wagtail_content_languages_setting` setting.

Wagtail will initially set up one `Locale` to act as the default language for all existing content.
This first locale will automatically pick the value from `WAGTAIL_CONTENT_LANGUAGES` that most closely matches the site primary language code defined in `LANGUAGE_CODE`.
If the primary language code is changed later, Wagtail will **not** automatically create a new `Locale` record or update an existing one.

Before internationalization is enabled, all pages use this primary `Locale` record.
This is to satisfy the database constraints and make it easier to switch internationalization on at a later date.

### Changing `WAGTAIL_CONTENT_LANGUAGES`

Languages can be added or removed from `WAGTAIL_CONTENT_LANGUAGES` over time.

Before removing an option from `WAGTAIL_CONTENT_LANGUAGES`, it's important that the `Locale`
record is updated to use a different content language or is deleted.
Any `Locale` instances that have invalid content languages are automatically filtered out from all
database queries making them unable to be edited or viewed.

### Methods and properties

```{eval-rst}
.. class:: Locale

    .. autoattribute:: language_code

    .. automethod:: get_default

    .. automethod:: get_active

    .. autoattribute:: language_name

    .. autoattribute:: language_name_local

    .. autoattribute:: language_name_localized

    .. autoattribute:: is_default

    .. autoattribute:: is_active

    .. autoattribute:: is_bidi

    .. automethod:: get_display_name
```

## `TranslatableMixin`

`TranslatableMixin` is an abstract model that can be added to any non-page Django model to make it translatable.
Pages already include this mixin, so there is no need to add it.

For a non-page model to be translatable in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](translatable_snippets).

### Database fields

```{eval-rst}
.. class:: TranslatableMixin

    .. attribute:: locale

        (Foreign Key to :class:`wagtail.models.Locale`)

        For pages, this defaults to the locale of the parent page.

    .. attribute:: translation_key

        (uuid)

        A UUID that is randomly generated whenever a new model instance is created.
        This is shared with all translations of that instance so can be used for querying translations.
```

The `translation_key` and `locale` fields have a unique key constraint to prevent the object from being translated into a language more than once.

```{note}
This is currently enforced via {attr}`~django.db.models.Options.unique_together` in `TranslatableMixin.Meta`, but may be replaced with a {class}`~django.db.models.UniqueConstraint` in `TranslatableMixin.Meta.constraints` in the future.

If your model defines a [`Meta` class](inv:django#ref/models/options) (either with a new definition or inheriting `TranslatableMixin.Meta` explicitly), be mindful when setting `unique_together` or {attr}`~django.db.models.Options.constraints`. Ensure that there is either a `unique_together` or a `UniqueConstraint` (not both) on `translation_key` and `locale`. There is a system check for this.
```

### Methods and properties

```{eval-rst}
.. class:: TranslatableMixin
    :no-index:

    .. automethod:: get_translations

    .. automethod:: get_translation

    .. automethod:: get_translation_or_none

    .. automethod:: has_translation

    .. automethod:: copy_for_translation

    .. automethod:: get_translation_model

    .. autoattribute:: localized
```

## `PreviewableMixin`

`PreviewableMixin` is a mixin class that can be added to any non-page Django model to allow previewing its instances.
Pages already include this mixin, so there is no need to add it.

For a non-page model to be previewable in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](wagtailsnippets_making_snippets_previewable).

### Methods and properties

```{eval-rst}
.. class:: PreviewableMixin

    .. autoattribute:: preview_modes

    .. autoattribute:: default_preview_mode

    .. autoattribute:: preview_sizes

    .. autoattribute:: default_preview_size

    .. automethod:: is_previewable

    .. automethod:: get_preview_context

    .. automethod:: get_preview_template

    .. automethod:: serve_preview
```

## `RevisionMixin`

`RevisionMixin` is an abstract model that can be added to any non-page Django model to allow saving revisions of its instances.
Pages already include this mixin, so there is no need to add it.

For a non-page model to be revisionable in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](wagtailsnippets_saving_revisions_of_snippets).

### Database fields

```{eval-rst}
.. class:: RevisionMixin

    .. attribute:: latest_revision

        (foreign key to :class:`~wagtail.models.Revision`)

        This points to the latest revision created for the object. This reference is stored in the database for performance optimization.
```

### Methods and properties

```{eval-rst}
.. class:: RevisionMixin
    :no-index:

    .. autoattribute:: _revisions

    .. autoattribute:: revisions

    .. automethod:: save_revision

    .. automethod:: get_latest_revision_as_object

    .. automethod:: with_content_json
```

## `DraftStateMixin`

`DraftStateMixin` is an abstract model that can be added to any non-page Django model to allow its instances to have unpublished changes.
This mixin requires {class}`~wagtail.models.RevisionMixin` to be applied. Pages already include this mixin, so there is no need to add it.

For a non-page model to have publishing features in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](wagtailsnippets_saving_draft_changes_of_snippets).

### Database fields

```{eval-rst}
.. class:: DraftStateMixin

    .. attribute:: live

        (boolean)

        A boolean that is set to ``True`` if the object is published.

        Note: this field defaults to ``True`` meaning that any objects that are created programmatically will be published by default.

    .. attribute:: live_revision

        (foreign key to :class:`~wagtail.models.Revision`)

        This points to the revision that is currently live.

    .. attribute:: has_unpublished_changes

        (boolean)

        A boolean that is set to ``True`` when the object is either in draft or published with draft changes.

    .. attribute:: first_published_at

        (date/time)

        The date/time when the object was first published.

    .. attribute:: last_published_at

        (date/time)

        The date/time when the object was last published.
```

### Methods and properties

```{eval-rst}
.. class:: DraftStateMixin
    :no-index:

    .. automethod:: publish

    .. automethod:: unpublish

    .. automethod:: with_content_json
```

## `LockableMixin`

`LockableMixin` is an abstract model that can be added to any non-page Django model to allow its instances to be locked.
Pages already include this mixin, so there is no need to add it. See [](wagtailsnippets_locking_snippets) for more details.

For a non-page model to be lockable in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](wagtailsnippets_locking_snippets).

### Database fields

```{eval-rst}
.. class:: LockableMixin

    .. attribute:: locked

        (boolean)

        A boolean that is set to ``True`` if the object is locked.

    .. attribute:: locked_at

        (date/time)

        The date/time when the object was locked.

    .. attribute:: locked_by

        (foreign key to user model)

        The user who locked the object.
```

### Methods and properties

```{eval-rst}
.. class:: LockableMixin
    :no-index:

    .. automethod:: get_lock

    .. automethod:: with_content_json
```

## `WorkflowMixin`

`WorkflowMixin` is a mixin class that can be added to any non-page Django model to allow its instances to be submitted to workflows.
This mixin requires {class}`~wagtail.models.RevisionMixin` and {class}`~wagtail.models.DraftStateMixin` to be applied. Pages already include this mixin, so there is no need to add it. See [](wagtailsnippets_enabling_workflows) for more details.

For a non-page model to have workflow features in the admin, it must also be [registered as a snippet](wagtailsnippets_registering). See also [](wagtailsnippets_enabling_workflows).

### Methods and properties

```{eval-rst}
.. class:: WorkflowMixin

    .. automethod:: get_default_workflow

    .. autoattribute:: has_workflow

    .. automethod:: get_workflow

    .. autoattribute:: _workflow_states

    .. autoattribute:: workflow_states

    .. autoattribute:: workflow_in_progress

    .. autoattribute:: current_workflow_state

    .. autoattribute:: current_workflow_task_state

    .. autoattribute:: current_workflow_task
```

(revision_model_ref)=

## `Revision`

Every time a page is edited, a new `Revision` is created and saved to the database. It can be used to find the full history of all changes that have been made to a page and it also provides a place for new changes to be kept before going live.

-   Revisions can be created from any instance of {class}`~wagtail.models.RevisionMixin` by calling its {meth}`~RevisionMixin.save_revision` method.
-   The content of the page is JSON-serialisable and stored in the {attr}`~Revision.content` field.
-   You can retrieve a `Revision` as an instance of the object's model by calling the {meth}`~Revision.as_object` method.

You can use the [`purge_revisions`](purge_revisions) command to delete old revisions that are no longer in use.

### Database fields

```{eval-rst}
.. class:: Revision

    .. attribute:: content_object

        (generic foreign key)

        The object this revision belongs to. For page revisions, the object is an instance of the specific class.

    .. attribute:: content_type

        (foreign key to :class:`~django.contrib.contenttypes.models.ContentType`)

        The content type of the object this revision belongs to. For page revisions, this means the content type of the specific page type.

    .. attribute:: base_content_type

        (foreign key to :class:`~django.contrib.contenttypes.models.ContentType`)

        The base content type of the object this revision belongs to. For page revisions, this means the content type of the :class:`~wagtail.models.Page` model.

    .. attribute:: object_id

        (string)

        The primary key of the object this revision belongs to.

    .. attribute:: created_at

        (date/time)

        The time the revision was created.

    .. attribute:: user

        (foreign key to user model)

        The user that created the revision.

    .. attribute:: content

        (dict)

        The JSON content for the object at the time the revision was created.
```

### Managers

```{eval-rst}
.. class:: Revision
    :no-index:

    .. attribute:: objects

        This default manager is used to retrieve all of the ``Revision`` objects in the database. It also provides a ``wagtail.models.RevisionsManager.for_instance`` method that lets you query for revisions of a specific object.

        Example:

        .. code-block:: python

            Revision.objects.all()
            Revision.objects.for_instance(my_object)

    .. attribute:: page_revisions

        This manager extends the default manager and is used to retrieve all of the ``Revision`` objects that belong to pages.

        Example:

        .. code-block:: python

            Revision.page_revisions.all()
```

### Methods and properties

```{eval-rst}
.. class:: Revision
    :no-index:

    .. automethod:: as_object

        This method retrieves this revision as an instance of its object's specific class. If the revision belongs to a page, it will be an instance of the :class:`~wagtail.models.Page`'s specific subclass.

    .. automethod:: is_latest_revision

        Returns ``True`` if this revision is the object's latest revision.

    .. automethod:: publish

        Calling this will copy the content of this revision into the live object. If the object is in draft, it will be published.

    .. autoattribute:: base_content_object

        This property returns the object this revision belongs to as an instance of the base class.
```

## `GroupPagePermission`

### Database fields

```{eval-rst}
.. class:: GroupPagePermission

    .. attribute:: group

        (foreign key to ``django.contrib.auth.models.Group``)

    .. attribute:: page

        (foreign key to :class:`~wagtail.models.Page`)
```

## `PageViewRestriction`

### Database fields

```{eval-rst}
.. class:: PageViewRestriction

    .. attribute:: page

        (foreign key to :class:`~wagtail.models.Page`)

    .. attribute:: password

        (text)

    .. attribute:: restriction_type

        (text)

        Options: none, password, groups, login
```

## `Orderable` (abstract)

### Database fields

```{eval-rst}
.. class:: Orderable

    .. attribute:: sort_order

        (number)
```

## `Workflow`

Workflows represent sequences of tasks that must be approved for an action to be performed on an object - typically publication.

### Database fields

```{eval-rst}
.. class:: Workflow

    .. attribute:: name

        (text)

        Human-readable name of the workflow.

    .. attribute:: active

        (boolean)

        Whether or not the workflow is active. Active workflows can be added to pages and snippets, and started. Inactive workflows cannot.
```

### Methods and properties

```{eval-rst}
.. class:: Workflow
    :no-index:

    .. automethod:: start

    .. autoattribute:: tasks

    .. automethod:: deactivate

    .. automethod:: all_pages
```

## `WorkflowState`

Workflow states represent the status of a started workflow on an object.

### Database fields

```{eval-rst}
.. class:: WorkflowState

    .. attribute:: content_object

        (generic foreign key)

        The object on which the workflow has been started. For page workflows, the object is an instance of the base ``Page`` model.

    .. attribute:: content_type

        (foreign key to :class:`~django.contrib.contenttypes.models.ContentType`)

        The content type of the object this workflow state belongs to. For page workflows, this means the content type of the specific page type.

    .. attribute:: base_content_type

        (foreign key to :class:`~django.contrib.contenttypes.models.ContentType`)

        The base content type of the object this workflow state belongs to. For page workflows, this means the content type of the :class:`~wagtail.models.Page` model.

    .. attribute:: object_id

        (string)

        The primary key of the object this revision belongs to.

    .. attribute:: workflow

        (foreign key to ``Workflow``)

        The workflow whose state the ``WorkflowState`` represents.

    .. attribute:: status

        (text)

        The current status of the workflow (options are ``WorkflowState.STATUS_CHOICES``)

    .. attribute:: created_at

        (date/time)

        When this instance of ``WorkflowState`` was created - when the workflow was started

    .. attribute:: requested_by

        (foreign key to user model)

        The user who started this workflow

    .. attribute:: current_task_state

        (foreign key to ``TaskState``)

        The ``TaskState`` model for the task the workflow is currently at: either completing (if in progress) or the final task state (if finished)
```

### Methods and properties

```{eval-rst}
.. class:: WorkflowState
    :no-index:

    .. attribute:: STATUS_CHOICES

        A tuple of the possible options for the ``status`` field, and their verbose names. Options are ``STATUS_IN_PROGRESS``, ``STATUS_APPROVED``,
        ``STATUS_CANCELLED`` and ``STATUS_NEEDS_CHANGES``.

    .. automethod:: update

    .. automethod:: get_next_task

    .. automethod:: cancel

    .. automethod:: finish

    .. automethod:: resume

    .. automethod:: copy_approved_task_states_to_revision

    .. automethod:: all_tasks_with_status

    .. automethod:: revisions
```

## `Task`

Tasks represent stages in a workflow that must be approved for the workflow to complete successfully.

### Database fields

```{eval-rst}
.. class:: Task

    .. attribute:: name

        (text)

        Human-readable name of the task.

    .. attribute:: active

        (boolean)

        Whether or not the task is active: active workflows can be added to workflows, and started. Inactive workflows cannot, and are skipped when in
        an existing workflow.

    .. attribute:: content_type

        (foreign key to ``django.contrib.contenttypes.models.ContentType``)

        A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` object that represents the specific model of this task.
```

### Methods and properties

```{eval-rst}
.. class:: Task
    :no-index:

    .. autoattribute:: workflows

    .. autoattribute:: active_workflows

    .. attribute:: task_state_class

        The specific task state class to generate to store state information for this task. If not specified, this will be ``TaskState``.

    .. automethod:: get_verbose_name

    .. autoattribute:: specific

    .. automethod:: start

    .. automethod:: on_action

    .. automethod:: user_can_access_editor

    .. automethod:: user_can_lock

    .. automethod:: user_can_unlock

    .. automethod:: locked_for_user

    .. automethod:: get_actions

    .. automethod:: get_task_states_user_can_moderate

    .. automethod:: deactivate

    .. automethod:: get_form_for_action

    .. automethod:: get_template_for_action

    .. automethod:: get_description
```

## `TaskState`

Task states store state information about the progress of a task on a particular revision.

### Database fields

```{eval-rst}
.. class:: TaskState

    .. attribute:: workflow_state

        (foreign key to :class:`~wagtail.models.WorkflowState`)

        The workflow state which started this task state.

    .. attribute:: revision

        (foreign key to :class:`~wagtail.models.Revision`)

        The revision this task state was created on.

    .. attribute:: task

        (foreign key to :class:`~wagtail.models.Task`)

        The task that this task state is storing state information for.

    .. attribute:: status

        (text)

        The completion status of the task on this revision. Options are available in ``TaskState.STATUS_CHOICES``)

    .. attribute:: content_type

        (foreign key to ``django.contrib.contenttypes.models.ContentType``)

        A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` object that represents the specific model of this task.

    .. attribute:: started_at

        (date/time)

        When this task state was created.

    .. attribute:: finished_at

        (date/time)

        When this task state was canceled, rejected, or approved.

    .. attribute:: finished_by

        (foreign key to user model)

        The user who completed (canceled, rejected, approved) the task.

    .. attribute:: comment

        (text)

        A text comment is typically added by a user when the task is completed.
```

### Methods and properties

```{eval-rst}
.. class:: TaskState
    :no-index:

    .. attribute:: STATUS_CHOICES

        A tuple of the possible options for the ``status`` field, and their verbose names. Options are ``STATUS_IN_PROGRESS``, ``STATUS_APPROVED``,
        ``STATUS_CANCELLED``, ``STATUS_REJECTED`` and ``STATUS_SKIPPED``.

    .. attribute:: exclude_fields_in_copy

        A list of fields not to copy when the ``TaskState.copy()`` method is called.

    .. autoattribute:: specific

    .. automethod:: approve

    .. automethod:: reject

    .. autoattribute:: task_type_started_at

    .. automethod:: cancel

    .. automethod:: copy

    .. automethod:: get_comment
```

## `WorkflowTask`

Represents the ordering of a task in a specific workflow.

### Database fields

```{eval-rst}
.. class:: WorkflowTask

    .. attribute:: workflow

        (foreign key to ``Workflow``)

    .. attribute:: task

        (foreign key to ``Task``)

    .. attribute:: sort_order

        (number)

        The ordering of the task in the workflow.
```

## `WorkflowPage`

Represents the assignment of a workflow to a page and its descendants.

### Database fields

```{eval-rst}
.. class:: WorkflowPage

    .. attribute:: workflow

        (foreign key to :class:`~wagtail.models.Workflow`)

    .. attribute:: page

        (foreign key to :class:`~wagtail.models.Page`)
```

## `WorkflowContentType`

Represents the assignment of a workflow to a Django model.

### Database fields

```{eval-rst}
.. class:: WorkflowContentType

    .. attribute:: workflow

        (foreign key to :class:`~wagtail.models.Workflow`)

    .. attribute:: content_type

        (foreign key to :class:`~django.contrib.contenttypes.models.ContentType`)

        A foreign key to the ``ContentType`` object that represents the model that is assigned to the workflow.

```

## `BaseLogEntry`

An abstract base class that represents a record of an action performed on an object.

### Database fields

```{eval-rst}
.. class:: BaseLogEntry

    .. attribute:: content_type

        (foreign key to ``django.contrib.contenttypes.models.ContentType``)

        A foreign key to the :class:`~django.contrib.contenttypes.models.ContentType` object that represents the specific model of this model.

    .. attribute:: label

        (text)

        The object title at the time of the entry creation

        Note: Wagtail will attempt to use ``get_admin_display_title`` or the string representation of the object passed to ``LogEntryManager.log_action``

    .. attribute:: user

        (foreign key to user model)

        A foreign key to the user that triggered the action.

    .. attribute:: revision

        (foreign key to :class:`Revision`)

        A foreign key to the current revision.

    .. attribute:: data

        (dict)

        The JSON representation of any additional details for each action.
        For example, source page id and title when copying from a page. Or workflow id/name and next step id/name on a workflow transition

    .. attribute:: timestamp

        (date/time)

        The date/time when the entry was created.

    .. attribute:: content_changed

        (boolean)

        A boolean that can be set to ``True`` when the content has changed.

    .. attribute:: deleted

        (boolean)

        A boolean that can set to ``True`` when the object is deleted. Used to filter entries in the Site History report.
```

### Methods and properties

```{eval-rst}
.. class:: BaseLogEntry
    :no-index:

    .. autoattribute:: user_display_name

    .. autoattribute:: comment

    .. autoattribute:: object_verbose_name

    .. automethod:: object_id
```

## `PageLogEntry`

Represents a record of an action performed on an {class}`Page`, subclasses {class}`BaseLogEntry`.

### Database fields

```{eval-rst}
.. class:: PageLogEntry

    .. attribute:: page

        (foreign key to :class:`Page`)

        A foreign key to the page the action is performed on.
```

## `Comment`

Represents a comment on a page.

### Database fields

```{eval-rst}
.. class:: Comment

    .. attribute:: page

        (parental key to :class:`Page`)

        A parental key to the page the comment has been added to.

    .. attribute:: user

        (foreign key to user model)

        A foreign key to the user who added this comment.

    .. attribute:: text

        (text)

        The text content of the comment.

    .. attribute:: contentpath

        (text)

        The path to the field or streamfield block the comment is attached to,
        in the form ``field`` or ``field.streamfield_block_id``.

    .. attribute:: position

        (text)

        An identifier for the position of the comment within its field. The format
        used is determined by the field.

    .. attribute:: created_at

        (date/time)

        The date/time when the comment was created.

    .. attribute:: updated_at

        (date/time)

        The date/time when the comment was updated.

    .. attribute:: revision_created

        (foreign key to :class:`Revision`)

        A foreign key to the revision on which the comment was created.

    .. attribute:: resolved_at

        (date/time)

        The date/time when the comment was resolved, if any.

    .. attribute:: resolved_by

        (foreign key to user model)

        A foreign key to the user who resolved this comment, if any.
```

## `CommentReply`

Represents a reply to a comment thread.

### Database fields

```{eval-rst}
.. class:: CommentReply

    .. attribute:: comment

        (parental key to :class:`Comment`)

        A parental key to the comment that started the thread.

    .. attribute:: user

        (foreign key to user model)

        A foreign key to the user who added this comment.

    .. attribute:: text

        (text)

        The text content of the comment.

    .. attribute:: created_at

        (date/time)

        The date/time when the comment was created.

    .. attribute:: updated_at

        (date/time)

        The date/time when the comment was updated.
```

## `PageSubscription`

Represents a user's subscription to email notifications about page events.
Currently only used for comment notifications.

### Database fields

```{eval-rst}
.. class:: PageSubscription

    .. attribute:: page

        (parental key to :class:`Page`)

    .. attribute:: user

        (foreign key to user model)

    .. attribute:: comment_notifications

        (boolean)

        Whether the user should receive comment notifications for all comments,
        or just comments in threads they participate in.
```
