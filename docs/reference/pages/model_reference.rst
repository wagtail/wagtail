===============
Model Reference
===============

.. automodule:: wagtail.wagtailcore.models

This document contains reference information for the model classes inside the ``wagtailcore`` module.

``Page``
========

Database fields
~~~~~~~~~~~~~~~

.. class:: Page

    .. attribute:: title

        (text)

        Human-readable title of the page.

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

    .. attribute:: seo_title

        (text)

        Alternate SEO-crafted title, for use in the page's ``<title>`` HTML tag.

    .. attribute:: search_description

        (text)

        SEO-crafted description of the content, used for search indexing. This is also suitable for the page's ``<meta name="description">`` HTML tag.

    .. attribute:: show_in_menus

        (boolean)

        Toggles whether the page should be included in site-wide menus.

        This is used by the :meth:`~wagtail.wagtailcore.query.PageQuerySet.in_menu` QuerySet filter.

Methods and properies
~~~~~~~~~~~~~~~~~~~~~

In addition to the model fields provided, ``Page`` has many properties and methods that you may wish to reference, use, or override in creating your own models. Those listed here are relatively straightforward to use, but consult the Wagtail source code for a full view of what's possible.

.. class:: Page

    .. autoattribute:: specific

    .. autoattribute:: specific_class

    .. autoattribute:: url

    .. autoattribute:: full_url

    .. automethod:: route

    .. automethod:: serve

    .. automethod:: get_context

    .. automethod:: get_template

    .. autoattribute:: preview_modes

    .. automethod:: serve_preview

    .. automethod:: get_ancestors

    .. automethod:: get_descendants

    .. automethod:: get_siblings

    .. attribute:: search_fields

        A list of fields to be indexed by the search engine. See Search docs :ref:`wagtailsearch_indexing_fields`

    .. attribute:: subpage_types

        A whitelist of page models which can be created as children of this page type. For example, a ``BlogIndex`` page might allow a ``BlogPage`` as a child, but not a ``JobPage``:

        .. code-block:: python

            class BlogIndex(Page):
                subpage_types = ['mysite.BlogPage', 'mysite.BlogArchivePage']

        The creation of child pages can be blocked altogether for a given page by setting it's subpage_types attribute to an empty array:

        .. code-block:: python

            class BlogPage(Page):
                subpage_types = []

    .. attribute:: parent_page_types

        A whitelist of page models which are allowed as parent page types. For example, a ``BlogPage`` may only allow itself to be created below the ``BlogIndex`` page:

        .. code-block:: python

            class BlogPage(Page):
                parent_page_types = ['mysite.BlogIndexPage']

        Pages can block themselves from being created at all by setting parent_page_types to an empty array (this is useful for creating unique pages that should only be created once):

        .. code-block:: python

            class HiddenPage(Page):
                parent_page_types = []

    .. automethod:: can_exist_under

    .. automethod:: can_create_at

    .. automethod:: can_move_to

    .. attribute:: password_required_template

        Defines which template file should be used to render the login form for Protected pages using this model. This overrides the default, defined using ``PASSWORD_REQUIRED_TEMPLATE`` in your settings. See :ref:`private_pages`

    .. attribute:: is_creatable

        Controls if this page can be created through the Wagtail administration. Defaults to True, and is not inherited by subclasses. This is useful when using `multi-table inheritance <https://docs.djangoproject.com/en/1.8/topics/db/models/#multi-table-inheritance>`_, to stop the base model from being created as an actual page.

``Site``
========

The ``Site`` model is useful for multi-site installations as it allows an administrator to configure which part of the tree to use for each hostname that the server responds on.

This configuration is used by the :class:`~wagtail.wagtailcore.middleware.SiteMiddleware` middleware class which checks each request against this configuration and appends the Site object to the Django request object.

Database fields
~~~~~~~~~~~~~~~

.. class:: Site

    .. attribute:: hostname

        (text)

        This is the hostname of the site, excluding the scheme, port and path.

        For example: ``www.mysite.com``

        .. note::

            If you're looking for how to get the root url of a site, use the :attr:`~Site.root_url` attribute.

    .. attribute:: port

        (number)

        This is the port number that the site responds on.

    .. attribute:: root_page

        (foreign key to :class:`~wagtail.wagtailcore.models.Page`)

        This is a link to the root page of the site. This page will be what appears at the ``/`` URL on the site and would usually be a homepage.

    .. attribute:: is_default_site

        (boolean)

        This is set to ``True`` if the site is the default. Only one site can be the default.

        The default site is used as a fallback in situations where a site with the required hostname/port couldn't be found.

Methods and properties
~~~~~~~~~~~~~~~~~~~~~~

.. class:: Site

    .. automethod:: find_for_request

    .. autoattribute:: root_url

        This returns the URL of the site. It is calculated from the :attr:`~Site.hostname` and the :attr:`~Site.port` fields.

        The scheme part of the URL is calculated based on value of the :attr:`~Site.port` field:

         - 80 = ``http://``
         - 443 = ``https://``
         - Everything else will use the ``http://`` scheme and the port will be appended to the end of the hostname (eg. ``http://mysite.com:8000/``)

    .. automethod:: get_site_root_paths

``PageRevision``
================

Every time a page is edited a new ``PageRevision`` is created and saved to the database. It can be used to find the full history of all changes that have been made to a page and it also provides a place for new changes to be kept before going live.

 - Revisions can be created from any :class:`~wagtail.wagtailcore.models.Page` object by calling its :meth:`~Page.save_revision` method
 - The content of the page is JSON-serialised and stored in the :attr:`~PageRevision.content_json` field
 - You can retrieve a ``PageRevision`` as a :class:`~wagtail.wagtailcore.models.Page` object by calling the :meth:`~PageRevision.as_page_object` method

Database fields
~~~~~~~~~~~~~~~

.. class:: PageRevision

    .. attribute:: page

        (foreign key to :class:`~wagtail.wagtailcore.models.Page`)

    .. attribute:: submitted_for_moderation

        (boolean)

        ``True`` if this revision is in moderation

    .. attribute:: created_at

        (date/time)

        This is the time the revision was created

    .. attribute:: user

        (foreign key to user model)

        This links to the user that created the revision

    .. attribute:: content_json

        (text)

        This field contains the JSON content for the page at the time the revision was created

Managers
~~~~~~~~

.. class:: PageRevision

    .. attribute:: objects

        This manager is used to retrieve all of the ``PageRevision`` objects in the database

        Example:

        .. code-block:: python

            PageRevision.objects.all()

    .. attribute:: submitted_revisions

        This manager is used to retrieve all of the ``PageRevision`` objects that are awaiting moderator approval

        Example:

        .. code-block:: python

            PageRevision.submitted_revisions.all()

Methods and properties
~~~~~~~~~~~~~~~~~~~~~~

.. class:: PageRevision

    .. automethod:: as_page_object

        This method retrieves this revision as an instance of its :class:`~wagtail.wagtailcore.models.Page` subclass.

    .. automethod:: approve_moderation

        Calling this on a revision that's in moderation will mark it as approved and publish it

    .. automethod:: reject_moderation

        Calling this on a revision that's in moderation will mark it as rejected

    .. automethod:: is_latest_revision

        Returns ``True`` if this revision is its page's latest revision

    .. automethod:: publish

        Calling this will copy the content of this revision into the live page object. If the page is in draft, it will be published.

``GroupPagePermission``
=======================

Database fields
~~~~~~~~~~~~~~~

.. class:: GroupPagePermission

    .. attribute:: group

        (foreign key to ``django.contrib.auth.models.Group``)

    .. attribute:: page

        (foreign key to :class:`~wagtail.wagtailcore.models.Page`)

    .. attribute:: permission_type

        (choice list)

``PageViewRestriction``
=======================

Database fields
~~~~~~~~~~~~~~~

.. class:: PageViewRestriction

    .. attribute:: page

        (foreign key to :class:`~wagtail.wagtailcore.models.Page`)

    .. attribute:: password

        (text)

``Orderable`` (abstract)
========================

Database fields
~~~~~~~~~~~~~~~

.. class:: Orderable

    .. attribute:: sort_order

        (number)
